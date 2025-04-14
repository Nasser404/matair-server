from scr.utils                  import remove_client, id_generator
from scr.enums                  import MESSAGE_TYPE, CLIENT_TYPE, PIECE_COLOR, ORB_STATUS ,INFORMATION_TYPE
from datetime                   import datetime
from random                     import choice
from scr.chess_game.chess_board import Chess_board

class Game :
    def __init__(self, server, game_id = id_generator(), local_game = False, virtual_game = False):
        self.board          = Chess_board()
        
        self.game_id        = game_id
        self.server         = server
        self.local_game     = local_game
        self.virtual_game   = virtual_game
        
        self.connected_orb_clients      = []
        self.connected_clients          = []
        self.connected_player_clients   = []
        self.connected_viewer_clients   = []
        
        self.client_colors = [None, None]
        self.chat_history  = []
        
        self.day_of_last_move   = datetime.now().timetuple().tm_yday
        self.closed             = False
    
    def get_info(self) -> dict : 
        white_client = self.get_client_instance(self.client_colors[PIECE_COLOR.WHITE])
        black_client = self.get_client_instance(self.client_colors[PIECE_COLOR.BLACK])
        
        if (self.virtual_game) or (self.local_game) :
            white_player_name = "" if white_client == None else white_client.get_name()
            black_player_name = "" if black_client == None else black_client.get_name()
            
            white_orb_name = ""
            if (len(self.connected_orb_clients)>0) and (self.local_game) : 
                white_orb_name    =  self.get_client_instance(self.connected_orb_clients[0]).get_name()
                
            black_orb_name    = white_orb_name
        else :
            white_orb_name = "" if white_client == None else white_client.get_name()
            black_orb_name = "" if black_client == None else black_client.get_name()
            
            
            
            white_player = None
            black_player = None
            if (len(self.connected_orb_clients) >=2) :
                white_player = self.get_client_instance(self.get_client_instance(self.client_colors[PIECE_COLOR.WHITE]).get_main_client())
                black_player = self.get_client_instance(self.get_client_instance(self.client_colors[PIECE_COLOR.BLACK]).get_main_client())
                
            white_player_name = "" if white_player == None else white_player.get_name()
            black_player_name = "" if black_player == None else black_player.get_name()
            
        data_packet = {
            'game_id'           : self.game_id,
            'local_game'        : self.local_game,
            'virtual_game'      : self.virtual_game,
            'status'            : self.game_ended(),
            'white_player'      : white_player_name,
            'black_player'      : black_player_name,
            'white_orb'         : white_orb_name,
            'black_orb'         : black_orb_name,
            'number_of_viewer'  : self.get_number_of_viewer(),
            'chat_history'      : self.chat_history,
            'winner'            : self.board.winner,
            'day_of_last_move'  : self.get_day_of_last_move(),
            'orbs_status'       : self.get_orbs_status()
            }
        return data_packet
        
        
    def get_number_of_player(self)   -> int         : return len(self.connected_player_clients)
    def get_number_of_viewer(self)   -> int         : return len(self.connected_viewer_clients)
    def get_game_id(self)            -> str         : return self.game_id
    def get_day_of_last_move(self)   -> int         : return self.day_of_last_move
    def get_board_string(self)       -> str         : return self.board.get_board_string()
    def is_local_game(self)          -> bool        : return self.local_game
    def is_virtual_game(self)        -> bool        : return self.virtual_game
    def get_data(self)               -> dict        : return self.board.get_board_data()
    def game_ended(self)             -> bool        : return self.board.game_ended
    def get_number_of_turn(self)     -> int         : return self.board.number_of_turn
    def get_game_turn(self)          -> PIECE_COLOR : return self.board.turn
    def game_joinable(self)          -> bool        : return (self.get_number_of_player() < 2) and (not self.game_ended())
    def get_number_of_orb(self)      -> int         : return len(self.connected_orb_clients)
    def is_move_legal(self, from_pos : list, to_pos : list) -> bool : return self.board.check_move_valid(from_pos, to_pos)
    
    def get_orbs_status(self) -> list :
        if (self.virtual_game) :
            return None
        elif (self.local_game) and (len(self.connected_orb_clients)>=1):
            orb_instance = self.get_client_instance(self.connected_orb_clients[0])
            return [orb_instance.get_status(), orb_instance.get_status()]
        elif(len(self.connected_orb_clients)>=2) :
            orb_1_instance = self.get_client_instance(self.connected_orb_clients[0])
            orb_2_instance = self.get_client_instance(self.connected_orb_clients[1])
            return [orb_1_instance.get_status(),orb_2_instance.get_status()] if orb_1_instance.get_color() == PIECE_COLOR.WHITE else  [orb_2_instance.get_status(), orb_1_instance.get_status()]
        return None
            
    def get_client_instance(self, client) : 
        if client == None : return None
        return self.server.clients_instance[client['id']]

    
    def update_clients_game_info(self) :
        info_packet =  {
        'type' : MESSAGE_TYPE.GAME_INFO,
        'info' : self.get_info()}
        self.server.send_packet_list(self.connected_clients, info_packet)
        
    def send_game_data(self, client, force_update = True) :
        client_instance = self.get_client_instance(client)
        if (client_instance == None) : return
          
        data_packet = {'type'           : MESSAGE_TYPE.GAME_DATA,
                       'info'           : self.get_info(),
                       'data'           : self.get_data(),
                       'board_string'   : self.get_board_string(),
                       'color'          : client_instance.get_color(),
                       'force_update'   : force_update
                       }
        
        client_instance.send_packet(data_packet)

    def connect_client(self, client) :
        client_instance = self.get_client_instance(client)
        client_type = client_instance.get_type()
        
        client_instance.set_connected_game_id(self.game_id)
        self.connected_clients.append(client)
        match(client_type) :
            case CLIENT_TYPE.ORB :
                if (not self.local_game) and (not self.virtual_game) : self.give_client_color(client)
                client_instance.update_clients_orb_data()
                self.connected_orb_clients.append(client)
                
            case CLIENT_TYPE.VIEWER :
                self.connected_viewer_clients.append(client)
                
            case CLIENT_TYPE.PLAYER :
                if (self.virtual_game) or (self.local_game) : self.give_client_color(client)
                else :
                    orb = client_instance.get_orb()
                    orb_color = orb.get_color()
                    client_instance.set_color(orb_color)
                    
                self.connected_player_clients.append(client)
               
        self.send_game_data(client)
        self.update_clients_game_info()
        
        
    def give_client_color(self, client) :
        color_choice = [i for i in range(len(self.client_colors)) if self.client_colors[i] == None]
        color = choice(color_choice)
        self.client_colors[color] = client
        
        client_instance = self.get_client_instance(client)
        client_instance.set_color(color)
        
    def disconnect_client(self, client) :
        client_instance = self.get_client_instance(client)
        client_instance_color    = client_instance.get_color()
        
        if (client_instance_color!=None) and (self.virtual_game or self.local_game) : self.client_colors[client_instance_color] = None # FREE THE COLOR USED BY THE PLAYER
        
        self.connected_clients          =  remove_client(client, self.connected_clients)
        self.connected_player_clients   =  remove_client(client, self.connected_player_clients)
        self.connected_viewer_clients   =  remove_client(client, self.connected_viewer_clients)
        self.connected_orb_clients      =  remove_client(client, self.connected_orb_clients)
        
        
        if (self.virtual_game) :                           # VIRTUAL GAME CLOSING REQUIEREMENT
            
            if (self.get_number_of_player() < 2) and (self.get_number_of_turn() > 4) :          # IF MORE THAN 4 MOVE HAVE BEEN MADE AND ONE PLAYER QUIT GAME
                self.board.game_ended = True                                                    # END THE GAME (NOT CLOSING JUST ENDING)
                self.board.winner = PIECE_COLOR.WHITE if (self.client_colors[PIECE_COLOR.BLACK] == None) else PIECE_COLOR.BLACK # SET THE PLAYER LEFT AS THE WINNVER
                
            if (self.get_number_of_player()<=0) :          # IF NO PLAYER LEFT IN THE GAME
                self.close()                               # CLOSE GAME
                return
            
        else :
            if (self.local_game) :                          # LOCAL GAME CLOSING REQUIEREMENT
                if (self.get_number_of_orb() < 1) :         # IF THE ORB HOSTING THE GAME HAS DISCONNECTED
                    self.close()                            # CLOSE GAME
                    return
            else :                                          # NORMAL GAME CLOSING REQUIEREMENT
                if (self.get_number_of_orb() < 2) :         # IF ONE OF THE ORB IN THE GAME HAS DISCONNECTED
                    self.close()                            # CLOSE GAME
                    return
               
            
        # IF DISCONNECTING CLIENT DID NOT CAUSE GAME CLOSING SEND CURRENT GAME INFORMATION TO LEFT CLIENT
        info = self.get_info()
        self.server.send_packet_list(self.connected_clients, {'type' :MESSAGE_TYPE.GAME_INFO,'info':info})
    
    
    def move_asked(self, client, move_data) :
        can_do_move = False # VAR USED TO KNOW IF GAME COULD DO MOVE OF PLAYER
        reason      = None  # IF COULD NOT DO MOVE OF PLAYER STORE THE REASON (INFORMATION TYPE ENUM)
        
        # GET CLIENT MOVE INFORMATION
        color    = move_data['color']
        from_pos = [int(i) for i in move_data['from']]
        to_pos   = [int(i) for i in move_data['to']]
        
        # FIND IF ALL THE ORB OF THE GAME ARE FREE
        orbs_free = True
        orbs_status = self.get_orbs_status()
        if (orbs_status != None) :
            for status in orbs_status :
                if (status == ORB_STATUS.OCCUPIED) :
                    orbs_free = False
                    break
            
        if (orbs_free) :                                                                                          # IF ALL THE ORBS OF THE GAME NOT OCCUPIED (PHYSICALLY MOVING)                                              
            if ((client['id'] in [_client_['id'] for _client_ in self.connected_player_clients])) :               # IF CLIENT IS A PLAYER IN GAME AND ORBS ARE FREE
                if (self.get_game_turn() == color) :                                                              # IF CLIENT COLOR IS CURRENT GMAE TURN
                    if (self.is_move_legal(from_pos, to_pos)) :                                                   # IF CLIENT MOVE IS LEGAL
                        
                        # DO THE MOVE OF THE CLIENT (AND GET SPECIAL MOVE {CASTLEING, PROMOTION, ETC..} TAHT HAPPENED DUE TO THIS MOVE)
                        special_move = self.board.move_piece(from_pos, to_pos) 
                        # TELL ALL OTHER CLIENT CONNECTED TO THE GAME TO REPLICATE MOVE
                        self.server.send_packet_list(self.connected_clients, {'type' : MESSAGE_TYPE.MOVE, 'from':from_pos, 'to':to_pos, 'special_move':special_move})
                        
                        # SET THE STATUS OF ALL ORBS OF THE GAME TO OCCUPIED
                        for orb_client in self.connected_orb_clients :
                            orb_instance = self.get_client_instance(orb_client)
                            if (orb_instance!=None) : orb_instance.set_status(ORB_STATUS.OCCUPIED)
                            
                        can_do_move = True
                        
                    else : reason = INFORMATION_TYPE.MOVE_NOT_LEGAL
                else : reason = INFORMATION_TYPE.NOT_PLAYER_TURN
            else :reason = INFORMATION_TYPE.NOT_GAME_PLAYER
        else : reason = INFORMATION_TYPE.ORB_NOT_READY
   
        # IF COULDNT DO THE MOVE OF CLIENT 
        if (not can_do_move) :
            self.send_game_data(client) # RESEND THE CLIENT THE GAME DATA SO THEY BE IN SYNC WITH CURRENT GAME STATE (MAYBE THEY REQUEST WAS NOT VALID BECAUSE THEY WERE NOT CORRECTLY SYNC)
            
            if (reason != None) :       # SEND THE REASON THE MOVE WAS NOT ACCEPTED
                self.server.send_packet(client, {'type' : MESSAGE_TYPE.INFORMATION, 'information' : reason})
           
           
            
    def add_message(self, message) :
        if (len(self.chat_history)> 50) : self.chat_history = self.chat_history[25:] # IF CHAT HISTORY SIZE > 50 CUT TO HALF
        self.chat_history.append(message)
        self.server.send_packet_list(self.connected_clients, {'type' : MESSAGE_TYPE.GAME_CHAT, 'message' : message})
            
    def close(self) :
        if self.closed : return
        
        # TELL ALL CLIENT CONNECTED TO GAME TO RUN THEIR disconnect_from_game() METHOD
        for client in self.connected_clients :
            client_instance = self.get_client_instance(client)
            client_instance.disconnect_from_game()
        
        # TELL SERVER TO CLOSE THIS GAME
        self.server.close_game(self.game_id)
        
        self.closed = True

                