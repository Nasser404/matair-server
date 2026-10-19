import logging
import os
import socket
import struct
import sys
from json               import dumps, loads
from threading          import RLock, Thread
from time               import time, sleep

from websocket_server   import WebsocketServer, CLOSE_STATUS_NORMAL, DEFAULT_CLOSE_REASON

from scr.config             import (SERVER_HOST, SERVER_PORT, SERVER_VERSION, PING_INTERVAL, CLIENT_TIMEOUT,
                                    SEND_TIMEOUT, LOG_LEVEL)
from scr.utils              import id_generator, CREDIT
from scr.enums              import MessageType, DisconnectReason, ClientType, InformationType, OrbStatus
from scr.server.game        import Game
from scr.client.game_client import GameClient
from scr.client.orb         import Orb
from scr.client.player      import Player
from scr.client.viewer      import Viewer

log = logging.getLogger("matair")

CLIENT_CLASSES      = {ClientType.ORB: Orb, ClientType.PLAYER: Player, ClientType.VIEWER: Viewer}
VIRTUAL_GAME_PREFIX = "VG"      # player codes starting with this join a virtual game (no orb)


def configure_logging(level: str = LOG_LEVEL):
    """Timestamped logs on stdout (same stream as the banner, so Docker keeps them in order)."""
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
                        stream=sys.stdout, force=True)
    logging.getLogger("websocket_server.websocket_server").addFilter(_LibraryLogFilter())


class _LibraryLogFilter(logging.Filter):
    """websocket_server logs "Client must always be masked." when a connection ends without a close frame
    (Wi-Fi lost, tab closed, timed-out client): the read returns nothing, the frame header is read as 0
    and "mask bit = 0" is reported. Say what it really means."""
    def filter(self, record):
        if record.getMessage() == "Client must always be masked.":
            record.msg, record.args = "Connection lost (closed without a WebSocket close frame)", ()
            record.levelno, record.levelname = logging.INFO, "INFO"
        return True


def _set_send_timeout(sock: socket.socket, seconds: float):
    """Make a send() blocked for more than `seconds` fail instead of hanging forever. Reads are not affected,
    so idle connections stay open."""
    try:
        if sys.platform == "win32":
            value = struct.pack("L", int(seconds * 1000))                               # DWORD, milliseconds
        else:
            value = struct.pack("ll", int(seconds), int(seconds % 1 * 1_000_000))       # struct timeval
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, value)
    except (OSError, struct.error):
        log.debug("Could not set the send timeout", exc_info=True)


class LockedWebsocketServer(WebsocketServer):
    """websocket_server runs every connection in its own thread. Its three internal callbacks (which also
    use the library's own unlocked client list) run here under one lock, so the server logic below is
    never executed by two threads at the same time.
    These are private methods of websocket-server: this relies on the version pinned in requirements.txt (0.6.4)."""

    def __init__(self, lock: RLock, **kwargs):
        self.lock = lock
        super().__init__(**kwargs)

    def _new_client_(self, handler):
        _set_send_timeout(handler.request, SEND_TIMEOUT)
        with self.lock:
            super()._new_client_(handler)

    def _client_left_(self, handler):
        with self.lock:
            super()._client_left_(handler)

    def _message_received_(self, handler, msg):
        with self.lock:
            super()._message_received_(handler, msg)

    def handle_error(self, request, client_address):
        # Errors raised inside the library itself (our callbacks catch their own): most often something that
        # isn't a WebSocket client (plain HTTP, port scanner, TLS probe), sometimes a connection broken mid-frame.
        # The connection is closed either way. One line instead of a full traceback.
        error = sys.exc_info()[1]
        detail = f"{type(error).__name__}: {error}" if str(error) else type(error).__name__
        log.warning("Connection from %s dropped by websocket_server (%s)", client_address[0], detail)
        log.debug("Traceback", exc_info=True)


class Server:
    def __init__(self):
        self.lock           = RLock()
        self.server         = None
        self.pending        = {}        # client id -> (client, connection time): connected, not identified yet
        self.clients        = {}        # client id -> Orb / Player / Viewer, in identification order
        self.orbs_by_id     = {}        # orb_id -> Orb
        self.games          = {}        # game_id -> Game
        self.broken_ids     = set()     # clients a send failed to: skipped, dropped at the next ping tick

        # message type -> handler(client, data)
        self.handlers = {
            MessageType.IDENTIFICATION         : self.handle_client_identification,
            MessageType.PONG                   : self.handle_pong,
            MessageType.ORB_DATA               : self.handle_orb_data,
            MessageType.ORB_CONNECT            : self.handle_orb_connect,
            MessageType.PLAYER_CONNECT         : self.handle_player_connect,
            MessageType.VIEWER_CONNECT         : self.handle_viewer_connect,
            MessageType.ORB_LIST               : self.handle_orb_list,
            MessageType.GAME_LIST              : self.handle_game_list,
            MessageType.ASK_MOVE               : self.handle_move_asked,
            MessageType.ORB_NEW_GAME           : self.handle_orb_new_game,
            MessageType.ORB_CONTINUE_GAME      : self.handle_orb_continue_game,
            MessageType.ORB_END_GAME           : self.handle_orb_end_game,
            MessageType.DISCONNECT_FROM_SERVER : self.handle_disconnect_request,
            MessageType.GAME_CHAT              : self.handle_game_chat,
        }

    def run(self):
        print(CREDIT, flush=True)
        self.server = LockedWebsocketServer(self.lock, host=SERVER_HOST, port=SERVER_PORT, loglevel=logging.WARNING)
        self.server.set_fn_new_client(self.handle_client_connect)
        self.server.set_fn_client_left(self.handle_client_disconnect)
        self.server.set_fn_message_received(self.handle_client_data)
        log.info("Mat@ir server %s listening on %s:%d", SERVER_VERSION, SERVER_HOST, SERVER_PORT)

        Thread(target=self.ping_loop, name="ping", daemon=True).start()
        self.server.run_forever()

    # ------------------------------------------------------------------ sending
    def send_packet(self, client, data: dict):
        if client is None or client['id'] in self.broken_ids:
            return
        try:
            # Serialize data (dict -> string) and send it
            self.server.send_message(client, dumps(data))
        except Exception:
            self._send_failed(client)

    def send_packet_list(self, client_list: list, data: dict):
        # Serialize data (dict -> string) once
        message = dumps(data)
        for client in client_list:
            if client is None or client['id'] in self.broken_ids:
                continue
            try:
                self.server.send_message(client, message)
            except Exception:
                self._send_failed(client)

    def _send_failed(self, client):
        # The socket is dead, or the client stopped reading and the send timed out (possibly halfway through a
        # frame). Either way nothing more can be sent to it: skip it from now on, the ping tick drops it.
        log.debug("Could not send to %s", self.label(client), exc_info=True)
        if client['id'] not in self.broken_ids:
            self.broken_ids.add(client['id'])
            log.info("Sending to %s failed, it will be dropped", self.label(client))

    def broadcast(self, game_clients, data: dict):
        """send_packet_list for Orb / Player / Viewer objects."""
        self.send_packet_list([game_client.client for game_client in game_clients], data)

    def disconnect_client(self, client, reason: DisconnectReason = DisconnectReason.NO_REASON):
        """Graceful disconnect: tell the client why, then send a close frame."""
        if client is None or client['id'] in self.broken_ids:
            return
        self.send_packet(client, {'type': MessageType.DISCONNECT_REASON, 'reason': reason})
        if client['id'] in self.broken_ids:     # that send just failed: don't wait again for the close frame
            return
        try:
            client["handler"].send_close(CLOSE_STATUS_NORMAL, DEFAULT_CLOSE_REASON)
        except Exception:
            self._send_failed(client)

    def terminate_client(self, client):
        """Abruptly close a connection (no close frame). Its cleanup runs right away, through finish()."""
        handler = client['handler']
        handler.keep_alive = False
        handler.finish()
        try:
            # close() alone doesn't close the socket while the reader thread's file object holds it:
            # shutdown() really ends the connection, so the reader thread and the peer both notice.
            handler.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        handler.connection.close()

    # ------------------------------------------------------------------ connection events
    def label(self, client) -> str:
        game_client = self.clients.get(client['id'])
        return str(game_client) if game_client is not None else f"client#{client['id']}"

    def client_as(self, client, cls=GameClient):
        """The client's Orb / Player / Viewer object, or None if it isn't identified as a `cls`."""
        game_client = self.clients.get(client['id'])
        return game_client if isinstance(game_client, cls) else None

    def forget(self, game_client: GameClient):
        """Remove a client from the registries (an orb only if the entry is still its own)."""
        self.clients.pop(game_client.id, None)
        if isinstance(game_client, Orb) and self.orbs_by_id.get(game_client.orb_id) is game_client:
            del self.orbs_by_id[game_client.orb_id]

    def handle_client_connect(self, client, server):
        try:
            self.pending[client['id']] = (client, time())
            # Tell newly connected client to identify (player, orb, viewer)
            self.send_packet(client, {"type": MessageType.IDENTIFICATION, "server_ver": SERVER_VERSION})
        except Exception:
            log.exception("Error while accepting client#%s", client['id'])

    def handle_client_disconnect(self, client, server):
        if client is None:
            return      # second finish() of a terminated connection: already cleaned up
        self.pending.pop(client['id'], None)
        game_client = self.clients.get(client['id'])
        if game_client is not None:
            log.info("%s disconnected", game_client)
            try:
                game_client.on_disconnected()
            except Exception:
                log.exception("Error while cleaning up %s", game_client)
            finally:
                self.forget(game_client)
        self.broken_ids.discard(client['id'])   # only now: its own cleanup must not try to send to it either

    def handle_client_data(self, client, server, message):
        if client is None:
            return
        # Remove null bytes, parse data (string -> dict). Bad input is ignored: nothing has been touched yet.
        message = message.strip().rstrip("\x00")
        try:
            data = loads(message) if message else None
        except (ValueError, RecursionError):
            data = None
        msg_type = data.get('type') if isinstance(data, dict) else None
        handler  = self.handlers.get(msg_type) if isinstance(msg_type, (int, float)) else None
        if handler is None:
            log.warning("Ignoring invalid message from %s: %.200r", self.label(client), message)
            return

        game_client = self.clients.get(client['id'])
        if game_client is not None:
            game_client.last_response = time()      # any valid message proves the client is alive
        if msg_type != MessageType.PONG:
            log.info("%s -> %s", self.label(client), data)

        try:
            handler(client, data)
        except Exception:
            # Unexpected: close this connection (its cleanup repairs the state) instead of guessing.
            log.exception("Error while handling %s from %s, closing its connection", data, self.label(client))
            self.terminate_client(client)

    # ------------------------------------------------------------------ ping / timeouts
    def ping_loop(self):
        log.info("Ping thread started (every %ss)", PING_INTERVAL)
        try:
            while True:
                sleep(PING_INTERVAL)
                try:
                    with self.lock:
                        self.ping_tick()
                except Exception:
                    log.exception("Ping tick failed")
        finally:
            # Unreachable in theory. Without this thread nobody is pinged or timed out any more, so exit and
            # let Docker (restart: unless-stopped) start a fresh server instead of running half-dead.
            log.critical("Ping thread stopped, exiting")
            os._exit(1)

    def ping_tick(self):
        now = time()
        to_drop = []
        for client, connected_at in list(self.pending.values()):
            if client['id'] in self.broken_ids:
                to_drop.append(client)
            elif now - connected_at > CLIENT_TIMEOUT:
                log.info("client#%s never identified, dropping it", client['id'])
                to_drop.append(client)
        for game_client in list(self.clients.values()):
            if game_client.id in self.broken_ids:
                to_drop.append(game_client.client)
            elif now - game_client.last_response > game_client.timeout:
                log.info("%s timed out", game_client)
                to_drop.append(game_client.client)
            else:
                game_client.send_packet({'type': MessageType.PING})

        for client in to_drop:
            self.terminate_client(client)
        # keep only the ids still connected (one may have broken during this tick's cleanup: next tick)
        self.broken_ids &= set(self.clients) | set(self.pending)

    # ------------------------------------------------------------------ games
    def new_game_id(self) -> str:
        game_id = id_generator()
        while game_id in self.games:
            game_id = id_generator()
        return game_id

    def create_game(self, game_id: str, local_game: bool = False, virtual_game: bool = False) -> Game:
        game = Game(self, game_id, local_game, virtual_game)
        self.games[game_id] = game
        log.info("Game %s created (%s)", game_id, "virtual" if virtual_game else "local" if local_game else "2 orbs")
        self.send_game_list_to_viewers()
        return game

    def remove_game(self, game: Game):
        if self.games.get(game.game_id) is not game:
            return
        log.info("Game %s closed", game.game_id)
        del self.games[game.game_id]
        self.send_game_list_to_viewers()

    def get_game_list(self) -> list:
        return [game.get_info() for game in self.games.values()]

    def send_game_list_to_viewers(self):
        viewers = [c for c in self.clients.values() if isinstance(c, Viewer)]
        self.broadcast(viewers, {'type': MessageType.GAME_LIST, 'game_info_list': self.get_game_list()})

    # ------------------------------------------------------------------ message handlers
    def handle_client_identification(self, client, data: dict):
        identifier = data.get('identifier')
        cls = CLIENT_CLASSES.get(identifier) if isinstance(identifier, (int, float)) else None
        if cls is None:
            log.warning("%s sent an unknown identifier %r", self.label(client), identifier)
            return

        previous = self.clients.get(client['id'])
        if previous is not None:        # same connection identifying again: start over, like a new connection
            log.info("%s identifies again", previous)
            try:
                previous.on_reidentified()
            finally:
                self.forget(previous)

        self.pending.pop(client['id'], None)
        game_client = cls(client, self)
        self.clients[client['id']] = game_client
        log.info("%s connected from %s", game_client, client['address'][0])
        game_client.on_identified()

    def handle_pong(self, client, data):
        pass    # last_response is refreshed for every message

    def handle_disconnect_request(self, client, data):
        self.disconnect_client(client)

    def handle_orb_connect(self, client, data):
        orb = self.client_as(client, Orb)
        if orb is None:
            return
        orb_id, orb_code = data['orb_id'], data['orb_code']

        # The ESP32 often reconnects before its old connection has timed out: the old one is dead, drop it now.
        previous = self.orbs_by_id.get(orb_id)
        if previous is not None and previous is not orb:
            log.warning("%s reconnected as %s, dropping the old connection", previous, orb)
            self.terminate_client(previous.client)
        # Same connection announcing a different id: forget the old one.
        if orb.orb_id is not None and self.orbs_by_id.get(orb.orb_id) is orb:
            del self.orbs_by_id[orb.orb_id]

        orb.orb_id = orb_id
        orb.name = orb_id
        orb.set_code(orb_code)
        self.orbs_by_id[orb_id] = orb

    def handle_orb_data(self, client, data):
        orb = self.client_as(client, Orb)
        if orb is None:
            return
        orb.set_status(data['status'])
        orb.set_code(data['orb_code'])

    def handle_player_connect(self, client, data):
        player = self.client_as(client, Player)
        if player is None:
            return
        player_orb_code = data['player_orb_code']
        player.name     = data['player_name']

        if player_orb_code.startswith(VIRTUAL_GAME_PREFIX):
            game = self.games.get(player_orb_code)
            if game is None:
                game = self.create_game(player_orb_code, virtual_game=True)
            if game.is_joinable():
                game.connect_client(player)
            else:
                self.disconnect_client(client, reason=DisconnectReason.GAME_NOT_JOINABLE)
            return

        orb = next((orb for orb in self.orbs_by_id.values() if orb.orb_code == player_orb_code), None)
        if orb is not None:
            orb.add_player(player)
        else:
            self.disconnect_client(client, reason=DisconnectReason.INVALID_ORB_CODE)

    def handle_viewer_connect(self, client, data):
        game = self.games.get(data['game_id'])
        if game is None:
            self.disconnect_client(client)
            return
        viewer = self.client_as(client, Viewer)
        if viewer is not None:
            game.connect_client(viewer)

    def handle_orb_list(self, client, data):
        orb_list = [orb.get_simple_data() for orb in self.orbs_by_id.values() if orb.is_new_game_possible()]
        self.send_packet(client, {'type': MessageType.ORB_LIST, 'orb_list': orb_list})

    def handle_game_list(self, client, data):
        self.send_packet(client, {'type': MessageType.GAME_LIST, 'game_info_list': self.get_game_list()})

    def handle_move_asked(self, client, data):
        game = self.games.get(data['game_id'])
        if game is None:
            self.disconnect_client(client)
            return
        game_client = self.client_as(client)
        if game_client is not None:
            game.move_asked(game_client, data)

    def handle_orb_new_game(self, client, data):
        player = self.client_as(client, Player)
        if player is None:
            return
        orb1 = self.orbs_by_id.get(data['id1'])
        orb2 = self.orbs_by_id.get(data['id2'])
        local_game = data['id1'] == data['id2']

        if orb1 is not None and orb2 is not None and orb1.is_new_game_possible() and orb2.is_new_game_possible():
            game = self.create_game(self.new_game_id(), local_game=local_game)
            orb1.add_main_player(player)
            game.connect_client(orb1)
            if not local_game:
                game.connect_client(orb2)
            game.connect_client(player)
            return

        # couldn't create the game: tell the player
        self.send_packet(client, {'type': MessageType.INFORMATION, 'information': InformationType.ORB_NOT_READY})

    def handle_orb_continue_game(self, client, data):
        # a second player joins the game running on an orb (local game), or a player comes back to it
        player = self.client_as(client, Player)
        orb    = self.orbs_by_id.get(data['id'])
        if player is None or orb is None or orb.game is None or orb.is_used() or player in orb.main_players:
            return
        orb.add_main_player(player)
        orb.game.connect_client(player)

    def handle_orb_end_game(self, client, data):
        orb = self.orbs_by_id.get(data['id'])
        if orb is not None and orb.status == OrbStatus.IDLE and orb.game is not None:
            orb.game.close()
            return
        # orb busy or not in a game: tell the client
        self.send_packet(client, {'type': MessageType.INFORMATION, 'information': InformationType.ORB_NOT_READY})

    def handle_game_chat(self, client, data):
        game    = self.games.get(data['game_id'])
        message = data['message']
        if game is None:
            self.disconnect_client(client)
        else:
            game.add_message(message)
