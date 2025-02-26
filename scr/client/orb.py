from .game_client import Game_client
from scr.config import CLIENT_TYPE, ORB_STATUS, MESSAGE_TYPE, DISCONNECT_REASONS, remove_client


class Orb(Game_client) :
    def __init__(self, client, server, type= CLIENT_TYPE.ORB):
        super().__init__(client, server, type)
        self.orb_code = None
        self.orb_id   = None
        self.orb_idle = False
        self.client_on_orb = []
        self.main_client   = []
        self.status                = ORB_STATUS.IDLE
        
    def connected_to_server(self) :
        self.send_packet({'type' : MESSAGE_TYPE.ORB_CONNECT})
    
    def disconnected_from_server(self) :
        print(f"orb id : {self.orb_id} DISCONNECTED FROM SERVER !!")
        
        self.disconnect_from_game()
        self.disconnect_all_client()
        del self.server.orbs[self.orb_id] # REMOVE SELF FROM LIST OF ORBS

        
    def get_orb_id(self) : return self.orb_id
    def get_code(self) : return self.orb_code
    def get_status(self) : return self.status
    
    def get_data(self) :
        data = {
            'id'        : self.orb_id,
            'code'      : self.orb_code,
            'in_game'   : self.is_in_game(),
            'status'    : self.get_status(),
            'used'      : self.is_used(),
            'game_id'   : self.connected_game_id,
            'game_info' : self.get_game_info(),
        }
        return data
    
    def get_simple_data(self) :
        data = {
            'id'        : self.orb_id,
            'code'      : self.orb_code,
            'in_game'   : self.is_in_game(),
            'status'    : self.get_status(),
        }
        return data
            
    def get_game_info(self) :
        game = self.get_game()
        return None if game == None else game.get_info()
    
    def get_main_client(self, n = 0) :
        return None if (len(self.main_client)-1 < n) else self.main_client[n]
       
    def is_used(self) :
        game = self.get_game()
        is_local_game = False
        if (game != None) : is_local_game = game.is_local_game()
        
        return len(self.main_client) >=2 if (is_local_game) else len(self.main_client) >= 1
    
    def is_new_game_possible(self) -> bool :

        return not self.is_used() and self.get_status() == ORB_STATUS.IDLE and not self.is_in_game()
    
    def set_code(self, code) : 
        self.orb_code = code
        self.update_data_to_client()
    def set_orb_id(self, orb_id)     : 
        self.orb_id       = orb_id
        self.name         = orb_id
        
    
    def set_status(self, status)     :
        self.status = status
        self.update_data_to_client()
    
    def update_data_to_client(self) :
        self.server.send_packet_list(self.client_on_orb, {'type' : MESSAGE_TYPE.ORB_DATA, 'orb_data' : self.get_data()})
        
    def reset(self) : self.send_packet({'type' : MESSAGE_TYPE.ORB_RESET}) 
    
    def set_client_as_main_client(self, client) : 
        self.main_client.append(client)
        self.update_data_to_client()
        
    
    def connect_client(self, client) :
        self.client_on_orb.append(client)
        
        player = self.get_client_instance(client)
        player.set_connected_orb_id(self.orb_id)
        print(self.main_client)
        player.send_packet({'type' : MESSAGE_TYPE.ORB_DATA, 'orb_data' : self.get_data()})
        
    def remove_client(self, client) :
       
        self.main_client    =  remove_client(client, self.main_client)
        self.client_on_orb  =  remove_client(client, self.client_on_orb)
        
        self.update_data_to_client()
    
    def disconnect_all_client(self) :
        
        for client in self.client_on_orb : self.ask_disconnect(client, reason=DISCONNECT_REASONS.ORB_DISCONNECTED)
        

    def disconnect_from_game(self) :
        self.disconnect_all_client()
        self.client_on_orb  = []
        self.main_client    = []
        game = self.get_game()
        if (game != None) : game.disconnect_client(self.client)
        self.set_color(color=None)
        self.set_connected_game_id(connected_game_id=None)