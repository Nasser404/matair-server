from scr.config             import SERVER_PORT, MAX_MISSED_PINGS, PING_INTERVAL, SERVER_VERSION
from scr.utils              import id_generator, remove_client, CREDIT
from scr.enums              import MESSAGE_TYPE, DISCONNECT_REASONS, CLIENT_TYPE, INFORMATION_TYPE, ORB_STATUS
from logging                import INFO
from json                   import dumps, loads
from websocket_server       import WebsocketServer, CLOSE_STATUS_NORMAL, DEFAULT_CLOSE_REASON
from .game                  import Game
from ..client.game_client   import Game_client
from ..client.orb           import Orb
from ..client.player        import Player
from ..client.viewer        import Viewer
from time                   import time, sleep
from threading              import Thread

class Server :
    def __init__(self):
        self.server             = None
        self.clients_instance   = {}       # dict linking all client using their client['id'] to their client instance 
        
        self.all_client         = []       # store all client currently connected
        self.players_client     = []       # store all players currently connected
        self.orbs_client        = []       # store all orbs currently connected
        self.viewers_client     = []       # store all viewers currently connected
        self.games              = {}       # dict linking all ongoing games (dict values) to their game_id (dict keys)
        self.orbs               = {}       # dict linking all orb clients (dict values) to their orb_id (dict keys)
        
        # Data handlers function
        self.data_handlers = {
            MESSAGE_TYPE.IDENTIFICATION         : self.handle_client_identification,    
            MESSAGE_TYPE.PONG                   : self.handle_pong,
            MESSAGE_TYPE.ORB_DATA               : self.handle_orb_data,
            MESSAGE_TYPE.ORB_CONNECT            : self.handle_orb_connect,
            MESSAGE_TYPE.PLAYER_CONNECT         : self.handle_player_connect,
            MESSAGE_TYPE.VIEWER_CONNECT         : self.handle_viewer_connect,
            MESSAGE_TYPE.ORB_LIST               : self.handle_orb_list,
            MESSAGE_TYPE.GAME_LIST              : self.handle_game_list,
            MESSAGE_TYPE.ASK_MOVE               : self.handle_move_asked,
            MESSAGE_TYPE.ORB_NEW_GAME           : self.handle_orb_new_game,
            MESSAGE_TYPE.ORB_CONTINUE_GAME      : self.handle_orb_continue_game,
            MESSAGE_TYPE.ORB_END_GAME           : self.handle_orb_end_game,
            MESSAGE_TYPE.DISCONNECT_FROM_SERVER : self.disconnect_client,
            MESSAGE_TYPE.GAME_CHAT              : self.handle_game_chat
        }
 
    
    def run(self) :
        # Initialize server
        print(CREDIT)
        self.server = WebsocketServer(host="0.0.0.0", port=SERVER_PORT, loglevel=INFO)
        self.server.set_fn_new_client(self.handle_client_connect)
        self.server.set_fn_client_left(self.handle_client_disconnect)
        self.server.set_fn_message_received(self.handle_client_data)
        
        # Start ping rhread
        ping_thread = Thread(target=self.send_ping, daemon=True)      
        ping_thread.start()
        
        # Start server thread
        self.server.run_forever()
        
    def close(self) :
        # Close the server
        self.server.shutdown_gracefully()
        
        
    def send_packet(self, client, data : dict) :
        if client == None : return
        try :
            # Serialize data (dict -> string)
            message = dumps(data)
            # Send data
            self.server.send_message(client, message) 
        except : pass
        #print(f"Sending : {message}")
    
    def send_packet_list(self, client_list : list, data : dict) :
        # Serialize data (dict -> string)
        message = dumps(data)
        
        for client in client_list : 
            if client == None : continue
            try :
                # Send data
                self.server.send_message(client, message)
            except :pass
        #print(f"Sending to list : {message}")    
        
        
    def handle_client_connect(self, client, server) :
        
        # Tell newly connected client to identify (player, orb, viewer)
        self.send_packet(client, {"type" : MESSAGE_TYPE.IDENTIFICATION, "server_ver" : SERVER_VERSION})
        self.all_client.append(client)
        
        #print(f"NEW CLIENT WITH ID : {client['id']} CONNECTED !")
        
        
    def handle_client_disconnect(self, client, server) :
        
        client_instance = self.get_client_instance(client)
        if (client_instance != None) :
            # run disconnected_from_server method of client instance of disconnected client
             client_instance.disconnected_from_server()   
        
        # remove client from all list
        self.remove_client_ref(client)

    def disconnect_client(self, client, data=None, reason = DISCONNECT_REASONS.NO_REASON) :
        if (client == None) : return
        try :
            # Try to disconnect client by sending close request to client (to try gracefully ending connection with client) 
            self.send_packet(client, data={'type' : MESSAGE_TYPE.DISCONNECT_REASON, 'reason' : reason})
            client["handler"].send_close(CLOSE_STATUS_NORMAL, DEFAULT_CLOSE_REASON)   
        except : pass
        
        
    def terminate_client(self, client) :
        if (client == None) : return
        # Abruptly close connection with client
        handler = client['handler']
        handler.keep_alive = False
        handler.finish()
        handler.connection.close()
    
         
    def remove_client_ref(self, client) :
        if (client == None) : return
        
        # Remove client from all list and dict
        print(f"removing client ref {client}")
        if client['id'] in self.clients_instance.keys() :  del self.clients_instance[client['id']]
        self.orbs_client   = remove_client(client, self.orbs_client)
        self.viewers_client= remove_client(client, self.viewers_client)
        self.players_client= remove_client(client, self.players_client)
        self.all_client    = remove_client(client, self.all_client)
        
        
    def handle_client_data(self, client, server, message) :
        if client == None : return
        # If data received was not from a known connected client, return
        if (client['id'] not in [_client_['id'] for _client_ in self.all_client]) : return
      
        # Remove null bytes
        message     = message.strip().rstrip("\x00") 
        # Parse date (string -> dict)
        data        = loads(message)
        
        # Run method corresponding to the type of data received (ENUM MESSAGE_TYPE)
        data_type   = data['type']
        self.data_handlers[data_type](client, data)    
        
        if (data_type != MESSAGE_TYPE.PONG): print(f"RECEIVED : {data}")
        
        
    def get_client_instance(self, client)-> Game_client :
        # Get client instance (orb class, player class or viewer class)
        return None if (client == None) else self.clients_instance.get(client['id'], None)
    
    
    def send_ping(self) :
        print("\nPING THREAD STARTED\n")
        while True:
            sleep(PING_INTERVAL)
            current_time = time()
            
            disconnected_clients = []

            for client_id, client_instance in self.clients_instance.items():  
                # get client last ping response
                last_response = client_instance.last_response

                if current_time - last_response > PING_INTERVAL * MAX_MISSED_PINGS:
                    # if client last ping response exceed a certain a time, timeout the client
                    print(f"Client {client_id} timed out")
                    disconnected_clients.append(client_instance.client)
                else:
                    # Send ping to client
                    try:
                        client_instance.send_packet({'type' : MESSAGE_TYPE.PING})
                    except Exception:
                        disconnected_clients.append(client_instance.client)

            for client in disconnected_clients:
                self.terminate_client(client)
                
    def handle_pong(self, client, data) :
        # response to ping received, update client last ping response
        client_instance = self.get_client_instance(client) 
        if client_instance != None :
            client_instance.last_response = time()     
       
    def create_game(self, game_id = id_generator(), local_game = False, virtual_game = False) -> Game:
        self.games[game_id] = Game(self, game_id, local_game, virtual_game)
        
        # send new game list to all viewer connected
        self.send_packet_list(self.viewers_client, {'type' : MESSAGE_TYPE.GAME_LIST, 'game_info_list' : self.get_game_list()})
        return self.games[game_id]
    
    def close_game(self, game_id) :
        if (game_id in self.games) :
            # close game
            print(f"closing game {game_id}")
            del self.games[game_id]
            
            # send new game list to all viewer connected
            self.send_packet_list(self.viewers_client, {'type' : MESSAGE_TYPE.GAME_LIST, 'game_info_list' : self.get_game_list()})
        
    def get_game_list(self) :
            game_info_list = []
            for game in self.games.values() :
                game_info_list.append(game.get_info())
            return game_info_list            
            
    def handle_game_list(self, client, data) :
        self.send_packet(client, {'type' : MESSAGE_TYPE.GAME_LIST, 'game_info_list' : self.get_game_list()})

    def handle_move_asked(self, client, data) :
        game_id = data['game_id']
        game = self.games.get(game_id, None)
        if (game == None) : self.disconnect_client(client)
        else : game.move_asked(client, data) 

    
    def handle_client_identification(self, client, data : dict) :
        print(data)
        identifier = data['identifier']
        # create and link a client instance (orb, player or viewer) to the client based on the identifier received from the client
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
        #run client instance connected_to_server() method
        client_instance.connected_to_server()
    


    def handle_player_connect(self, client, data) :
        player_orb_code = data['player_orb_code']
        player_name     = data['player_name']
        
        player = self.get_client_instance(client)
        player.set_name(player_name)
        
        ###################################### VIRTUAL GAME #############################
        if player_orb_code[0:2] == "VG":                                                        # IF CODE START WITH VG
            
            # GET GAME IF GAME EXIST OR CREATE NEW GAME
            new_game = self.create_game(player_orb_code, False, True) if (self.games.get(player_orb_code, None) == None) else self.games.get(player_orb_code) 
            
            if (new_game.game_joinable()) : new_game.connect_client(client)                     # IF GAME JOINABLE CONNECT PLAYER TO GAME
            else : self.disconnect_client(client, reason=DISCONNECT_REASONS.GAME_NOT_JOINABLE)  # IF GAME NOT JOINABLE DISCONNECT CLIENT 
            return                                                                              # EXIT FUNCTION
        #################################################################################
        
        player_orb = None
        # TRY TO FIND THE ORB CORRESPONDING TO THE ORB CODE THE PLAYER ENTERED
        for orb_client in self.orbs_client :
            orb = self.get_client_instance(orb_client)
            orb_code = orb.get_code()
            if (orb_code == player_orb_code) :
                player_orb = orb
                break
        
        if (player_orb!=None) : player_orb.connect_client(client)                  # IF THE ORB CODE CORRESPOND TO A ORB, CONNECT PLAYER TO ORB
        else : self.disconnect_client(client, reason=DISCONNECT_REASONS.INVALID_ORB_CODE) # ELSE DISCONNECT CLIENT
    
    def handle_orb_connect(self, client, data) :
        orb_id = data['orb_id']
        orb_code = data['orb_code']
        orb_board = data['orb_board']
        
        orb = self.get_client_instance(client)
        orb.set_orb_id(orb_id)
        orb.set_code(orb_code)

        
        self.orbs[orb_id] = client # ADD SELF TO LIST OF ORBS
        
    def handle_orb_data(self, client, data) :
        orb         = self.get_client_instance(client)
        status      = data['status']
        orb_code    = data['orb_code']
        orb.set_status(status)
        orb.set_code(orb_code)
        
    def handle_orb_list(self, client, data) :
        orb_list = []
        for orb_client in self.orbs_client :
            orb = self.get_client_instance(orb_client)
            if (orb.is_new_game_possible()) : orb_list.append(orb.get_simple_data())
        self.send_packet(client, {'type': MESSAGE_TYPE.ORB_LIST, 'orb_list' : orb_list})
        
    def handle_orb_new_game(self, client, data) :
        orb1_id = data['id1']
        orb2_id = data['id2']
        
        local_game = orb1_id == orb2_id
        
        orb1_client = self.orbs.get(orb1_id, None)
        orb2_client = self.orbs.get(orb2_id, None)
        
        orb1_instance = self.get_client_instance(orb1_client)
        orb2_instance = self.get_client_instance(orb2_client)
        
    
        if (orb1_instance!=None) and (orb2_instance!=None) : # THE TWO GIVEN ORB ID ARE VALID
            if (orb1_instance.is_new_game_possible()) and (orb2_instance.is_new_game_possible()) : 
                print("\n\n\nGAME IS POSSIBLE")
                game = self.create_game(id_generator(), local_game, False)
                orb1_instance.set_client_as_main_client(client)
                game.connect_client(orb1_client)
                if (not local_game) : game.connect_client(orb2_client)
                game.connect_client(client)
                return # IF COULD CREATE GAME, EXIT FUNCTION HERE
        
        #IF COULDNT CREATE GAME SEND INFORMATION TO CLIENT WHO TRIED THAT HIS ATTEMPT HAS FAILED
        self.send_packet(client, {'type' : MESSAGE_TYPE.INFORMATION, 'information' : INFORMATION_TYPE.ORB_NOT_READY})
           
    
    def handle_orb_continue_game(self, client, data) :
        orb_id          = data['id']
        orb_client      = self.orbs.get(orb_id, None)
        orb_instance    = self.get_client_instance(orb_client)
        
        if (orb_instance!=None) :
            if (not orb_instance.is_used()) :
                orb_instance.set_client_as_main_client(client)
                game = orb_instance.get_game()
                game.connect_client(client)
            

    def handle_orb_end_game(self, client, data) :
        orb_id          = data['id']
        orb_client      = self.orbs.get(orb_id, None)
        orb_instance    = self.get_client_instance(orb_client)
        
        if (orb_instance!=None) and (orb_instance.get_status() == ORB_STATUS.IDLE) : # IF ORB IS FREE AND VALID
            if (orb_instance.is_in_game()) :
                game = orb_instance.get_game()
                game.close()
                return#  IF COULD CLOSE GAME, EXIT FUNCTION HERE
        
        #IF COULDNT CLOSE GAME SEND INFORMATION TO CLIENT WHO TRIED
        self.send_packet(client, {'type' : MESSAGE_TYPE.INFORMATION, 'information' : INFORMATION_TYPE.ORB_NOT_READY})
    
    def handle_viewer_connect(self, client, data) :
        # send game list
        game_id = data['game_id']
        game = self.games.get(game_id, None)
        if (game == None) : self.disconnect_client(client)
        else : game.connect_client(client)
    
    def handle_game_chat(self, client, data) :
        game_id = data['game_id']
        message = data['message']
        game = self.games.get(game_id, None)
        if (game == None) : self.disconnect_client(client)
        else : game.add_message(message)
        