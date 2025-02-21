from .game_client import Game_client
from scr.config import CLIENT_TYPE, MESSAGE_TYPE

class Viewer(Game_client) :
    def __init__(self, client, server, type= CLIENT_TYPE.VIEWER):
        super().__init__(client, server, type)
        
        
    def connected_to_server(self) :
        
        self.send_packet({'type' : MESSAGE_TYPE.VIEWER_CONNECT, 'game_info_list' : self.server.get_game_list()})
    
    def disconnected_from_server(self) :
        self.disconnect_from_game()
        

         