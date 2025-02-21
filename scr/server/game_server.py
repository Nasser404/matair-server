from scr.config import MESSAGE_TYPE, DISCONNECT_REASONS, CLIENT_TYPE, SERVER_PORT, id_generator,remove_client
import logging
import json
from websocket_server import WebsocketServer
from .game import Game
from ..client.game_client import Game_client
from ..client.orb import Orb
from ..client.player import Player
from ..client.viewer import Viewer
FAL = 8
class Server :
    def __init__(self):
        self.server = None
        self.client_list      = [];         # store all clients currently connected
        self.clients_instance = {};         # struct linking all client using their id to their client instance 
        
        self.players_client    = [];      # store all players currently connected
        self.orbs_client       = [];      # store all orbs currently connected
        self.viewers_client    = [];      # store all viewers currently connected
        self.games = {}                   # store all ongoing games
        self.orbs  = {}                   # store all orbs ref using their orb_id
        
        
        self.data_handlers = {
            MESSAGE_TYPE.IDENTIFICATION      : self.handle_client_identification,    
            MESSAGE_TYPE.PONG                : None,
            MESSAGE_TYPE.ORB_DATA            : None,
            MESSAGE_TYPE.ORB_CONNECT         : self.handle_orb_connect,
            MESSAGE_TYPE.PLAYER_CONNECT      : None,
            MESSAGE_TYPE.VIEWER_CONNECT      : None,
            MESSAGE_TYPE.ORB_LIST            : None,
            MESSAGE_TYPE.GAME_LIST           : None,
            MESSAGE_TYPE.MOVE                : None,
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
        message = json.dumps(data)
        self.server.send_message(client, message)  
    
    def send_packet_list(self, client_list : list, data : dict) :
        message = json.dumps(data)
        for client in client_list : self.server.send_message(client, message)
        
    def handle_client_connect(self, client, server) :
        self.send_packet(client, {"type" : MESSAGE_TYPE.IDENTIFICATION})
        print(f"{client['id']} connected !")
        
        
    def handle_client_disconnect(self, client, server) :
        self.disconnect_client(client)
    
    def handle_client_data(self, client, server, message) :
        message = message.strip().rstrip("\x00") 
        
        data = json.loads(message)
        data_type = data['type']
        print(data)
        self.data_handlers[data_type](client, data)
        
        
        
    def disconnect_client(self, client, data=None, reason = DISCONNECT_REASONS.NO_REASON) :
        client_instance = self.get_client_instance(client)
        
        if (client_instance != None) :
            if (reason != DISCONNECT_REASONS.NO_REASON) :
                client_instance.send_packet( {'type' : MESSAGE_TYPE.DISCONNECT_REASON, 'reason' : reason})
                
            client_instance.disconnected_from_server()    
        
        if client['id'] in self.clients_instance.keys() :  del self.clients_instance[client['id']]
        self.client_list   = remove_client(client, self.client_list)
        self.orbs_client   = remove_client(client, self.orbs_client)
        self.viewers_client= remove_client(client, self.viewers_client)
        self.players_client= remove_client(client, self.players_client)
        
        print(f"{client['id']} diconnected !")
        
        
    
    def get_client_instance(self, client)-> Game_client :
    
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
        print(print(self.clients_instance))
    
    
    def get_id(self, client) : return client['id']
    
    def create_game(self, game_id = id_generator(), local_game = False, virtual_game = False) :
        self.games[game_id] = Game(self, game_id, local_game, virtual_game)
        self.send_packet_list(self.viewers_client, self.get_game_list())
    
    def close_game(self, game_id) :
        game = self.games[game_id]
        game.close()
        del self.games[game_id]
        self.send_packet_list(self.viewers_client, self.get_game_list())
    
    def get_game_list(self) :
            game_info_list = []
            for game in self.games.items() :
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
        
    