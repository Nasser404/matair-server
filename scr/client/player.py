from .game_client import Game_client
from scr.config import CLIENT_TYPE, MESSAGE_TYPE

class Player(Game_client) :
    def __init__(self, client, server, type= CLIENT_TYPE.PLAYER):
        super().__init__(client, server, type)
        self.connnected_orb_id = None
        
        
    def connected_to_server(self) :
        self.send_packet({'type' : MESSAGE_TYPE.PLAYER_CONNECT})
    
    def disconnected_from_server(self) :
        self.disconnect_from_game()
        orb = self.get_orb()
        if (orb != None) : orb.remove_client(self.client)
        
     
    def get_orb(self):
        if (self.connnected_orb_id==None) : return None
        orb_client = self.server.orbs.get(self.connnected_orb_id, None)
        return self.get_client_instance(orb_client)
    
    def set_connected_orb_id(self, orb_id) : self.connnected_orb_id = orb_id
         