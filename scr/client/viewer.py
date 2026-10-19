from scr.client.game_client import GameClient
from scr.enums              import ClientType, MessageType


class Viewer(GameClient):
    type = ClientType.VIEWER

    def on_identified(self):
        # send the list of ongoing games
        self.send_packet({'type': MessageType.VIEWER_CONNECT, 'game_info_list': self.server.get_game_list()})

    def leave_game(self):
        # a viewer leaving its game (or the game closing) is sent back to the menu
        self.kick()
        super().leave_game()

    def on_reidentified(self):
        super().leave_game()    # starting over on the same connection: leave without being kicked
