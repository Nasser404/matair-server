from scr.config import MESSAGE_TYPE, DISCONNECT_REASONS, id_generator,CLIENT_TYPE, PIECE_COLOR, remove_client
from datetime import datetime
from random import choice
class Game :
    def __init__(self, server, game_id = id_generator(), local_game = False, virtual_game = False):
        self.board = None
        #self.board.
        
        self.game_id = game_id
        self.server = server
        self.local_game = local_game
        self.virtual_game = virtual_game
        
        self.connected_orb_clients = []
        self.connected_clients     = []
        self.connected_player_clients = []
        self.connected_viewer_clients = []
        self.day_of_last_move         = datetime.now().timetuple().tm_yday
        
        self.client_colors = [None, None]
        self.chat_history  = []
        
    
    def get_info(self) : 
        white_client = self.get_client_instance(self.client_colors[PIECE_COLOR.WHITE])
        black_client = self.get_client_instance(self.client_colors[PIECE_COLOR.WHITE])
        if (self.virtual_game) or (self.local_game) :
            white_player_name = "" if white_client == None else white_client.get_name()
            black_player_name = "" if black_client == None else black_client.get_name()
            
            white_orb_name    = "" if (not self.local_game) else self.get_client_instance(self.client_colors[0]).get_name()
            black_orb_name    = white_orb_name
        else :
            white_orb_name = "" if white_client == None else white_client.get_name()
            black_orb_name = "" if black_client == None else black_client.get_name()
            
            white_player = self.get_client_instance(self.connected_orb_clients[0]).get_main_client()
            black_player = self.get_client_instance(self.connected_orb_clients[1]).get_main_client()
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
        }
        return data_packet
        
        
    def get_number_of_player(self)  : return len(self.connected_player_clients)
    def get_number_of_viewer(self)  : return len(self.conencted_viewer_clients)
    def get_game_id(self)           : return self.game_id
    def get_day_of_last_move(self)  : return self.get_day_of_last_move
    def get_board_string(self)      : return self.board.get_board_string()
    def is_local_game(self)         : return self.local_game
    def is_virtual_game(self)       : return self.virtual_game
    def get_data(self)  -> dict     : return self.board.get_board_data()
    def game_ended(self)-> bool     : return self.board.game_ended
    def get_number_of_turn(self)    : return self.board.number_of_turn
    def get_game_turn(self)         : return self.board.turn
    def is_move_legal(self, from_pos : list, to_pos : list) : return self.board.check_move(from_pos, to_pos)
      
    def get_client_instance(self, client) : return self.server.clients_instance[client['id']]
    
    def game_joinable(self) :
        return (self.get_number_of_player < 2) and (not self.game_ended())
    

    def connect_client(self, client) :
        client_instance = self.get_client_instance(client)
        client_type = client_instance.get_type()
        
        client_instance.set_connected_game_id(self.game_id)
        
        match(client_type) :
            case CLIENT_TYPE.ORB :
                if (not self.local_game) and (not self.virtual_game) : self.give_client_color(client)
                self.connected_orb_clients.append(client)
                
            case CLIENT_TYPE.VIEWER :
                self.conencted_viewer_clients.append(client)
                
            case CLIENT_TYPE.PLAYER :
                if (self.virtual_game) or (self.local_game) : self.give_client_color(client)
                else :
                    orb = client_instance.get_orb()
                    orb_color = orb.get_color()
                    client_instance.set_color(orb_color)
                    
                self.connected_player_clients.append(client)

        data_packet = {'type' : MESSAGE_TYPE.GAME_DATA,
                  'info' : self.get_info(),
                  'data' : self.get_data(),
                  'board_string' : self.get_board_string(),
                  'color' :  client_instance.get_color(),
                  'force_update' : True}
        
        client_instance.send_packet(data_packet)
        
        info_packet =  {
            'type' : MESSAGE_TYPE.GAME_INFO,
            'info' : self.get_info()}
        
        other_client_list =  [d for d in self.connected_clients if d.get('id') != client['id']]
        self.server.send_packet_list(other_client_list, info_packet)
        
    def give_client_color(self, client) :
        
        color_choice = [i for i in range(len(self.client_colors)) if self.client_colors[i] == None]
        color = choice(color_choice)
        self.client_colors[color] = client
        
        client_instance = self.get_client_instance(client)
        client_instance.set_color(color)
        
    def disconnect_client(self, client) :
        
        if (client['id'] in [_client_['id'] for _client_ in self.connected_orb_clients]) : self.server.close_game(self.game_id)
        
        
        client_instance = self.get_client_instance(client)
        client_instance_color    = client_instance.get_color()
        if (client_instance_color!=None) : self.client_colors[client_instance_color] = None
        
        self.connected_clients          =  remove_client(client, self.connected_clients)
        self.connected_player_clients   =  remove_client(client, self.connected_player_clients)
        self.connected_viewer_clients   =  remove_client(client, self.connected_viewer_clients)
        self.connected_orb_clients      =  remove_client(client, self.connected_orb_clients)
        
        if (self.get_number_of_player() < 2) and (self.get_number_of_turn() > 4) :
            self.board.game_ended = True
            self.board.winner = PIECE_COLOR.WHITE if (self.client_colors[PIECE_COLOR.BLACK] == None) else PIECE_COLOR.BLACK
            
            
        if (self.get_number_of_player()<=0) : 
            self.server.close_game(self.game_id)
            return
        
        self.server.send_packet_list(self.connected_clients, {'type' :MESSAGE_TYPE.GAME_INFO,'info':self.get_info()})
    
    
    def move_asked(self, client, move_data) :
        can_do_move = False
        
        color    = move_data['color']
        from_pos = move_data['from']
        to_pos   = move_data['to']
        
        if ((client['id'] in [_client_['id'] for _client_ in self.connected_player_clients])):
            if (self.get_game_turn() == color) :
                if (self.is_move_legal(from_pos, to_pos)) :
                    self.board.move_piece(from_pos, to_pos)
                    self.server.send_packet_list(self.connected_clients, {'type' : MESSAGE_TYPE.MOVE, 'from':from_pos, 'to':to_pos})
                    can_do_move = True
        
        if (not can_do_move) :
            client_instance = self.get_client_instance(client)
            data_packet = {'type' : MESSAGE_TYPE.GAME_DATA,
            'info' : self.get_info(),
            'data' : self.get_data(),
            'board_string' : self.get_board_string(),
            'color' :  client_instance.get_color(),
            'force_update' : True}
            client_instance.send_packet(data_packet)
            
    def close(self) :
        for client in self.connected_clients :
            client_instance = self.get_client_instance(client)
            client_instance.disconnect_from_game()

                