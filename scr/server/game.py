import logging
from datetime                   import datetime
from random                     import choice

from scr.chess_game.chess_board import ChessBoard
from scr.enums                  import MessageType, ClientType, PieceColor, OrbStatus, InformationType

log = logging.getLogger("matair")

FORFEIT_MIN_TURNS   = 4     # in a virtual game, leaving after more turns than this loses the game
CHAT_HISTORY_LIMIT  = 50    # above this, the oldest half of the chat is dropped


def _name(client) -> str:
    return "" if client is None else client.name


def _today() -> int:
    return datetime.now().timetuple().tm_yday


def _parse_move(move_data: dict):
    """(color, from_pos, to_pos) as ints, or None if the message is malformed."""
    try:
        color    = int(move_data['color'])
        from_pos = [int(i) for i in move_data['from']]
        to_pos   = [int(i) for i in move_data['to']]
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if len(from_pos) != 2 or len(to_pos) != 2:
        return None
    return color, from_pos, to_pos


class Game:
    """One chess game and the clients attached to it.

    - orb game:     two orbs, each with its player (colors belong to the orbs)
    - local game:   one orb, both players play on it (colors belong to the players)
    - virtual game: no orb at all, joined with a "VG..." code (colors belong to the players)
    """

    def __init__(self, server, game_id: str, local_game: bool = False, virtual_game: bool = False):
        self.board          = ChessBoard()
        self.server         = server
        self.game_id        = game_id
        self.local_game     = local_game
        self.virtual_game   = virtual_game

        self.clients        = []        # everyone in the game, in join order
        self.orbs           = []
        self.players        = []
        self.viewers        = []
        self.colors         = [None, None]      # client holding white / black

        self.chat_history       = []
        self.day_of_last_move   = _today()
        self.closed             = False

    # ------------------------------------------------------------------ info
    def is_joinable(self) -> bool:
        return len(self.players) < 2 and not self.board.game_ended

    def get_info(self) -> dict:
        if self.virtual_game or self.local_game:
            white_player, black_player = self.colors
            orb = self.orbs[0] if (self.local_game and self.orbs) else None
            white_orb = black_orb = orb
        else:
            white_orb, black_orb = self.colors
            both_orbs = len(self.orbs) >= 2
            white_player = white_orb.main_player() if both_orbs else None
            black_player = black_orb.main_player() if both_orbs else None

        return {
            'game_id'           : self.game_id,
            'local_game'        : self.local_game,
            'virtual_game'      : self.virtual_game,
            'status'            : self.board.game_ended,
            'white_player'      : _name(white_player),
            'black_player'      : _name(black_player),
            'white_orb'         : _name(white_orb),
            'black_orb'         : _name(black_orb),
            'number_of_viewer'  : len(self.viewers),
            'chat_history'      : self.chat_history,
            'winner'            : self.board.winner,
            'day_of_last_move'  : self.day_of_last_move,
            'orbs_status'       : self.get_orbs_status(),
        }

    def get_orbs_status(self) -> list | None:
        """[white orb status, black orb status], or None when there is no orb."""
        if self.virtual_game:
            return None
        if self.local_game:
            return [self.orbs[0].status] * 2 if self.orbs else None
        if len(self.orbs) >= 2:
            first, second = self.orbs[0], self.orbs[1]
            return [first.status, second.status] if first.color == PieceColor.WHITE else [second.status, first.status]
        return None

    def orbs_ready(self) -> bool:
        statuses = self.get_orbs_status()
        return statuses is None or OrbStatus.OCCUPIED not in statuses

    def update_clients_game_info(self):
        self.server.broadcast(self.clients, {'type': MessageType.GAME_INFO, 'info': self.get_info()})

    def send_game_data(self, client, force_update: bool = True):
        client.send_packet({
            'type'          : MessageType.GAME_DATA,
            'info'          : self.get_info(),
            'data'          : self.board.get_board_data(),
            'board_string'  : self.board.get_board_string(),
            'color'         : client.color,
            'force_update'  : force_update,
        })

    # ------------------------------------------------------------------ clients
    def connect_client(self, client):
        if client.game is self:             # already in: just resend the game (e.g. a viewer refreshing)
            self.send_game_data(client)
            return
        if client.game is not None:         # joining another game on the same connection: leave the old one first
            old_game = client.game
            for orb in old_game.orbs:
                if client in orb.main_players:
                    orb.remove_main_player(client)
            old_game.remove_client(client)

        client.game = self
        self.clients.append(client)
        match client.type:
            case ClientType.ORB:
                if not (self.local_game or self.virtual_game):
                    self.give_color(client)
                client.update_players_orb_data()
                self.orbs.append(client)

            case ClientType.VIEWER:
                self.viewers.append(client)

            case ClientType.PLAYER:
                if self.virtual_game or self.local_game:
                    self.give_color(client)
                else:   # orb game: the player takes the color of the orb it plays on
                    orb = next((o for o in self.orbs if client in o.main_players), None)
                    client.color = None if orb is None else orb.color
                self.players.append(client)

        self.send_game_data(client)
        self.update_clients_game_info()

    def give_color(self, client):
        free = [color for color in (PieceColor.WHITE, PieceColor.BLACK) if self.colors[color] is None]
        color = choice(free)
        self.colors[color] = client
        client.color = color

    def remove_client(self, client):
        if client.color is not None and self.colors[client.color] is client:
            self.colors[client.color] = None        # free the color for whoever joins next
        self.clients = [c for c in self.clients if c is not client]
        self.players = [c for c in self.players if c is not client]
        self.viewers = [c for c in self.viewers if c is not client]
        self.orbs    = [c for c in self.orbs    if c is not client]

        if self.closed:
            return

        if self.virtual_game:
            # a player leaving a game that really started loses it
            if len(self.players) < 2 and self.board.number_of_turn > FORFEIT_MIN_TURNS and not self.board.game_ended:
                self.board.game_ended = True
                self.board.winner = PieceColor.WHITE if self.colors[PieceColor.BLACK] is None else PieceColor.BLACK
            if not self.players:
                self.close()
                return
        elif len(self.orbs) < (1 if self.local_game else 2):   # the game can't go on without its orb(s)
            self.close()
            return

        self.update_clients_game_info()

    def close(self):
        if self.closed:
            return
        self.closed = True
        for client in list(self.clients):
            client.leave_game()
        self.server.remove_game(self)

    # ------------------------------------------------------------------ moves & chat
    def turn_owner(self, color: int):
        """Client allowed to move `color`: the player holding it, or in an orb game the main player of the orb holding it."""
        holder = self.colors[color]
        if holder is None or self.local_game or self.virtual_game:
            return holder
        return holder.main_player()

    def move_asked(self, client, move_data: dict):
        move   = _parse_move(move_data)
        reason = None

        if not self.orbs_ready():                       # an orb is still physically moving pieces
            reason = InformationType.ORB_NOT_READY
        elif client not in self.players:
            reason = InformationType.NOT_GAME_PLAYER
        elif move is None:
            reason = InformationType.MOVE_NOT_LEGAL
        else:
            color, from_pos, to_pos = move
            if color != self.board.turn or self.turn_owner(color) is not client:
                reason = InformationType.NOT_PLAYER_TURN
            elif not self.board.is_move_valid(from_pos, to_pos):
                reason = InformationType.MOVE_NOT_LEGAL
            else:
                self.play_move(from_pos, to_pos)
                return

        # refused: resync the client (it may simply be out of date), then tell it why
        self.send_game_data(client)
        client.send_packet({'type': MessageType.INFORMATION, 'information': reason})

    def play_move(self, from_pos: list[int], to_pos: list[int]):
        from_pos = [from_pos[0] % 8, from_pos[1]]       # cylinder: columns wrap
        to_pos   = [to_pos[0] % 8, to_pos[1]]
        special_move = self.board.move_piece(from_pos, to_pos)
        self.day_of_last_move = _today()
        log.info("Game %s: move %s -> %s", self.game_id, from_pos, to_pos)

        # every client replicates the move, then the orbs are busy until they report IDLE again
        self.server.broadcast(self.clients, {'type': MessageType.MOVE, 'from': from_pos, 'to': to_pos,
                                             'special_move': special_move})
        for orb in self.orbs:
            orb.set_status(OrbStatus.OCCUPIED)

    def add_message(self, message):
        if len(self.chat_history) > CHAT_HISTORY_LIMIT:
            del self.chat_history[:CHAT_HISTORY_LIMIT // 2]
        self.chat_history.append(message)
        self.server.broadcast(self.clients, {'type': MessageType.GAME_CHAT, 'message': message})
