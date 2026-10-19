from scr.client.game_client import GameClient
from scr.enums              import ClientType, MessageType


class Player(GameClient):
    type = ClientType.PLAYER

    def __init__(self, client, server):
        super().__init__(client, server)
        self.orb = None             # last Orb this player joined with a code (None in virtual games)

    def on_identified(self):
        # ask the client to send its name and orb code
        self.send_packet({'type': MessageType.PLAYER_CONNECT})

    def on_disconnected(self):
        self.leave_game()
        if self.orb is not None:
            self.orb.remove_player(self)
        # other orbs this connection joined earlier with another code
        for orb in list(self.server.orbs_by_id.values()):
            if orb is not self.orb and (self in orb.connected_players or self in orb.main_players):
                orb.remove_player(self)
