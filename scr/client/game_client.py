from scr.enums      import DISCONNECT_REASONS
from time           import time

class Game_client() :
    def __init__(self, client, server, type = None):
        self.server             = server
        self.client             = client
        self.type               = type
        self.id                 = client['id']
        self.connected_game_id  = None
        self.color              = None
        self.name               = ""
        self.last_response      = time()

    def send_packet(self, data : dict) :
        self.server.send_packet(self.client, data)
    
    def get_client(self)            -> dict : return self.client
    def get_type(self)              -> int  : return self.type
    def get_connected_game_id(self) -> str  : return self.connected_game_id
    def get_color(self)             -> int  : return self.color

    def get_name(self)              -> str  : return self.name
    def is_in_game(self)            -> bool : return (self.connected_game_id != None)
    def get_game(self)                      : return None if (self.connected_game_id == None) else self.server.games.get(self.connected_game_id, None)
    
    def get_client_instance(self, client : dict)   :
        return None if client == None else self.server.clients_instance.get(client['id'], None)
    

    def set_color(self, color : int)                         : self.color = color
    def set_name(self, name : str)                           : self.name  = name
    def set_connected_game_id(self, connected_game_id : str) : self.connected_game_id = connected_game_id
    
    def ask_disconnect(self, client : dict, reason : DISCONNECT_REASONS = DISCONNECT_REASONS.NO_REASON) : self.server.disconnect_client(client, reason=reason)
    
    def disconnect_from_game(self) :
        game = self.get_game()
        if (game != None) : game.disconnect_client(self.client)
        self.set_color(color=None)
        self.set_connected_game_id(connected_game_id=None)
        
      
        #self.send_packet({'type' : MESSAGE_TYPE.GAME_DISCONNECT})
    
    
     


        