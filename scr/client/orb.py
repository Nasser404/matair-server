from scr.client.game_client import GameClient
from scr.config             import ORB_TIMEOUT
from scr.enums              import ClientType, OrbStatus, MessageType, DisconnectReason


class Orb(GameClient):
    """The physical spherical chess board (ESP32)."""
    type    = ClientType.ORB
    timeout = ORB_TIMEOUT       # can't answer pings while its motors are moving pieces

    def __init__(self, client, server):
        super().__init__(client, server)
        self.orb_id             = None
        self.orb_code           = None              # code the players type to join (changes on every reconnect)
        self.status             = OrbStatus.OCCUPIED    # unusable until the orb reports IDLE
        self.connected_players  = []                # players who joined this orb with its code
        self.main_players       = []                # those playing the orb's game (2 in a local game)

    def on_identified(self):
        self.send_packet({'type': MessageType.ORB_CONNECT})

    def on_disconnected(self):
        if self.orb_id is not None:     # never registered: nothing to clean up
            self.leave_game()

    # ------------------------------------------------------------------ state
    def main_player(self):
        return self.main_players[0] if self.main_players else None

    def is_used(self) -> bool:
        needed = 2 if (self.game is not None and self.game.local_game) else 1
        return len(self.main_players) >= needed

    def is_new_game_possible(self) -> bool:
        return not self.is_used() and self.status == OrbStatus.IDLE and self.game is None

    def get_data(self) -> dict:
        return {
            'id'        : self.orb_id,
            'code'      : self.orb_code,
            'in_game'   : self.game is not None,
            'status'    : self.status,
            'used'      : self.is_used(),
            'game_id'   : None if self.game is None else self.game.game_id,
            'game_info' : None if self.game is None else self.game.get_info(),
        }

    def get_simple_data(self) -> dict:
        return {
            'id'        : self.orb_id,
            'code'      : self.orb_code,
            'in_game'   : self.game is not None,
            'status'    : self.status,
        }

    def set_code(self, code: str):
        self.orb_code = code
        self.update_players_orb_data()

    def set_status(self, status: OrbStatus):
        self.status = status
        self.update_players_orb_data()
        if self.game is not None:
            self.game.update_clients_game_info()

    def update_players_orb_data(self):
        self.server.broadcast(self.connected_players, {'type': MessageType.ORB_DATA, 'orb_data': self.get_data()})

    def reset(self):
        """Ask the orb to physically put the pieces back to the starting position."""
        self.send_packet({'type': MessageType.ORB_RESET})

    # ------------------------------------------------------------------ players
    def add_player(self, player):
        if player not in self.connected_players:
            self.connected_players.append(player)
        player.orb = self
        player.send_packet({'type': MessageType.ORB_DATA, 'orb_data': self.get_data()})

    def add_main_player(self, player):
        self.main_players.append(player)
        self.update_players_orb_data()

    def remove_main_player(self, player):
        self.main_players = [p for p in self.main_players if p is not player]
        self.update_players_orb_data()

    def remove_player(self, player):
        self.main_players       = [p for p in self.main_players if p is not player]
        self.connected_players  = [p for p in self.connected_players if p is not player]
        self.update_players_orb_data()

    def kick_players(self):
        for player in list(self.connected_players):
            player.kick(DisconnectReason.ORB_DISCONNECTED)

    def leave_game(self):
        # Game over (or orb gone): send the players back to the menu and reset the physical board.
        self.kick_players()
        self.connected_players  = []
        self.main_players       = []
        self.reset()
        super().leave_game()
