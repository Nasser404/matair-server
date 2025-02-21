from scr.config import MESSAGE_TYPE, DISCONNECT_REASONS, CLIENT_TYPE, SERVER_PORT, id_generator,remove_client
import logging
import json
from websocket_server import WebsocketServer,CLOSE_STATUS_NORMAL,DEFAULT_CLOSE_REASON
from .game import Game
from ..client.game_client import Game_client
from ..client.orb import Orb
from ..client.player import Player
from ..client.viewer import Viewer
FAL = 8
class Server :
    def __init__(self):
        self.server = None
        self.clients_instance = {};         # struct linking all client using their id to their client instance 
        
        self.players_client    = [];      # store all players currently connected
        self.orbs_client       = [];      # store all orbs currently connected
        self.viewers_client    = [];      # store all viewers currently connected
        self.games = {}                   # store all ongoing games
        self.orbs  = {}                   # store all orbs ref using their orb_id
        
        
        self.data_handlers = {
            MESSAGE_TYPE.IDENTIFICATION      : self.handle_client_identification,    
            MESSAGE_TYPE.PONG                : None,
            MESSAGE_TYPE.ORB_DATA            : self.handle_orb_data,
            MESSAGE_TYPE.ORB_CONNECT         : self.handle_orb_connect,
            MESSAGE_TYPE.PLAYER_CONNECT      : self.handle_player_connect,
            #MESSAGE_TYPE.VIEWER_CONNECT      : self.handle_v,
            MESSAGE_TYPE.ORB_LIST            : self.handle_orb_list,
            MESSAGE_TYPE.GAME_LIST           : self.handle_game_list,
            MESSAGE_TYPE.ASK_MOVE            : self.handle_move_asked,
            MESSAGE_TYPE.ORB_NEW_GAME        : None,
            MESSAGE_TYPE.ORB_CONTINUE_GAME   : None,
            MESSAGE_TYPE.ORB_END_GAME        : None,
            MESSAGE_TYPE.DISCONNECT_FROM_SERVER : self.disconnect_client   
        }
 
    
    def create(self) :
        self.server = WebsocketServer(host="0.0.0.0", port=SERVER_PORT, loglevel=logging.INFO)
        self.server.set_fn_new_client(self.handle_client_connect)
        self.server.set_fn_client_left(self.handle_client_disconnect)
        self.server.set_fn_message_received(self.handle_client_data)
        self.server.run_forever()
        
    def close(self) :
        self.server.shutdown_gracefully()
        
    def send_packet(self, client, data : dict) :
        print(f"Sending : {data}")
        message = json.dumps(data)
        self.server.send_message(client, message)  
    
    def send_packet_list(self, client_list : list, data : dict) :
        print(f"Sending to list : {data}")
        message = json.dumps(data)
        for client in client_list : self.server.send_message(client, message)
        
    def handle_client_connect(self, client, server) :
        print(f"{len(self.server.clients)} client connected !")
        self.send_packet(client, {"type" : MESSAGE_TYPE.IDENTIFICATION})
    
        print(f"{client['id']} connected !")
        
        
    def handle_client_disconnect(self, client, server) :

        client_instance = self.get_client_instance(client)
        if (client_instance != None) :
             client_instance.disconnected_from_server()   
        self.remove_client_ref(client)

    
    def handle_client_data(self, client, server, message) :
        message = message.strip().rstrip("\x00") 
        
        data = json.loads(message)
        data_type = data['type']
        print(f"RECEIVED : {data}")
        self.data_handlers[data_type](client, data)
        
    def remove_client_ref(self, client) :
        
        if client['id'] in self.clients_instance.keys() :  del self.clients_instance[client['id']]
        self.orbs_client   = remove_client(client, self.orbs_client)
        self.viewers_client= remove_client(client, self.viewers_client)
        self.players_client= remove_client(client, self.players_client)
        
    def disconnect_client(self, client, data=None, reason = DISCONNECT_REASONS.NO_REASON) :
        client["handler"].send_close(CLOSE_STATUS_NORMAL, DEFAULT_CLOSE_REASON)
  
 
        

        
        
    
    def get_client_instance(self, client)-> Game_client :
        if (client == None) : return None
        return self.clients_instance.get(client['id'], None)
    
    def handle_client_identification(self, client, data : dict) :
        identifier = data['identifier']
        match identifier :
            case CLIENT_TYPE.ORB : 
                self.orbs_client.append(client)
                self.clients_instance[client['id']] = Orb(client, self)
            case CLIENT_TYPE.PLAYER :
                self.players_client.append(client)
                self.clients_instance[client['id']] = Player(client, self)
            case CLIENT_TYPE.VIEWER :
                self.viewers_client.append(client)
                self.clients_instance[client['id']] = Viewer(client, self)
                
        client_instance = self.get_client_instance(client)
        client_instance.connected_to_server()
    
    

    
    def create_game(self, game_id = id_generator(), local_game = False, virtual_game = False) :
        self.games[game_id] = Game(self, game_id, local_game, virtual_game)
        self.send_packet_list(self.viewers_client, {'type' : MESSAGE_TYPE.GAME_LIST, 'game_info_list' : self.get_game_list()})
        return self.games[game_id]
    
    def close_game(self, game_id) :
        game = self.games[game_id]
        game.close()
        del self.games[game_id]
        self.send_packet_list(self.viewers_client, {'type' : MESSAGE_TYPE.GAME_LIST, 'game_info_list' : self.get_game_list()})
    
    def get_game_list(self) :
            game_info_list = []
            for game in self.games.values() :
                game_info_list.append(game.get_info())
            return game_info_list
    
    def handle_orb_connect(self, client, data) :
        orb_id = data['orb_id']
        orb_code = data['orb_code']
        orb_board = data['orb_board']
        
        orb = self.get_client_instance(client)
        orb.set_orb_id(orb_id)
        orb.set_code(orb_code)
        orb.reset()
        self.orbs[orb_id] = client
        
    def handle_orb_data(self, client, data) :
        orb = self.get_client_instance(client)
        status = data['status']
        orb_code = data['orb_code']
        orb.set_status(status)
        orb.set_code(orb_code)
        
    def handle_move_asked(self, client, data) :
        game_id = data['game_id']
        game = self.games.get(game_id, None)
        if (game == None) : self.disconnect_client(client)
        else : game.move_asked(client, data)
        
    def handle_orb_list(self, client, data) :
        orb_list = []
        for orb_client in self.orbs_client :
            orb = self.get_client_instance(orb_client)
            orb_list.append(orb.get_simple_data())
        self.send_packet(client, {'type': MESSAGE_TYPE.ORB_LIST, 'orb_list' : orb_list})
        
    def handle_player_connect(self, client, data) :
        player_orb_code = data['player_orb_code']
        player_name     = data['player_name']
        
        player = self.get_client_instance(client)
        player.set_name(player_name)
        
        ###################################### VIRTUAL GAME #############################
        if player_orb_code[0:2] == "VG":
            new_game = self.create_game(player_orb_code, False, True) if (self.games.get(player_orb_code, None) == None) else self.games.get(player_orb_code)
            if (new_game.game_joinable()) : new_game.connect_client(client)
            else : self.disconnect_client(client, reason=DISCONNECT_REASONS.GAME_NOT_JOINABLE)
            return
        #################################################################################
        
        player_orb = None
        for orb_client in self.orbs_client :
            orb = self.get_client_instance(orb_client)
            orb_code = orb.get_code()
            if(orb_code == player_orb_code) :
                player_orb = orb
                break
        
        if (player_orb!=None) : player_orb.connect_client(client)
        else : self.disconnect_client(client, DISCONNECT_REASONS.INVALID_ORB_CODE)
        

    def handle_game_list(self, client, data) :
        self.send_packet(client, self.get_game_list())