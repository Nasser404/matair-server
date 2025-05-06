from scr.chess_game.piece.pawn      import Pawn
from scr.chess_game.piece.knight    import Knight
from scr.chess_game.piece.bishop    import Bishop
from scr.chess_game.piece.rook      import Rook
from scr.chess_game.piece.queen     import Queen
from scr.chess_game.piece.king      import King
from scr.enums                      import PIECE_COLOR, PIECE_TYPE, SPECIAL_MOVES
from scr.utils                      import wrap_pos
from numpy                          import array_equal

class Chess_board() :
    def __init__(self):
        self.grid = [[None for i in range(8)] for j in range(8)]
     
        self.captured_pieces = {"white" : {"Pawn":0, "Rook":0, "Knight": 0, "Bishop" : 0, "Queen":0, "King":0}, 
                                "black" : {"Pawn":0, "Rook":0, "Knight": 0, "Bishop" : 0, "Queen":0, "King":0}}
        
        self.players_names = {"white" : "",
                              "black" : ""}
        
        self.orbs_names    = {"white" : "",
                              "black" : ""}
        
        self.turn           = PIECE_COLOR.WHITE
        self.number_of_turn = 0
        self.checked        = None
        self.is_false_board = False
        self.game_ended     = False
        self.winner         = None
        self.possible_moves = [[], []]
        self.square_reached = [[], []]
        
        for i in range(8) :
            self.add_piece(PIECE_TYPE.PAWN, PIECE_COLOR.BLACK, [i, 1])
            self.add_piece(PIECE_TYPE.PAWN, PIECE_COLOR.WHITE, [i, 6])
        #Rook
        self.add_piece(PIECE_TYPE.ROOK, PIECE_COLOR.BLACK, [0, 0])
        self.add_piece(PIECE_TYPE.ROOK, PIECE_COLOR.BLACK, [7, 0])
        self.add_piece(PIECE_TYPE.ROOK, PIECE_COLOR.WHITE, [0, 7])
        self.add_piece(PIECE_TYPE.ROOK, PIECE_COLOR.WHITE, [7, 7])
        
        # Knight
        self.add_piece(PIECE_TYPE.KNIGHT, PIECE_COLOR.BLACK, [1, 0])
        self.add_piece(PIECE_TYPE.KNIGHT, PIECE_COLOR.BLACK, [6, 0])
        self.add_piece(PIECE_TYPE.KNIGHT, PIECE_COLOR.WHITE, [1, 7])
        self.add_piece(PIECE_TYPE.KNIGHT, PIECE_COLOR.WHITE, [6, 7])
        
        # Bishop
        self.add_piece(PIECE_TYPE.BISHOP, PIECE_COLOR.BLACK, [2, 0])
        self.add_piece(PIECE_TYPE.BISHOP, PIECE_COLOR.BLACK, [5, 0])
        self.add_piece(PIECE_TYPE.BISHOP, PIECE_COLOR.WHITE, [2, 7])
        self.add_piece(PIECE_TYPE.BISHOP, PIECE_COLOR.WHITE, [5, 7])

        # Queen
        self.add_piece(PIECE_TYPE.QUEEN, PIECE_COLOR.BLACK, [3, 0])
        self.add_piece(PIECE_TYPE.QUEEN, PIECE_COLOR.WHITE, [3, 7])
        
        # King
        self.add_piece(PIECE_TYPE.KING, PIECE_COLOR.BLACK, [4, 0])
        self.add_piece(PIECE_TYPE.KING, PIECE_COLOR.WHITE, [4, 7])
        
                
        self.calculate_all_moves()

    def get_grid(self) : return self.grid 
    
    def add_piece(self, type : PIECE_TYPE, color : PIECE_COLOR, pos : list[int]) :
        x = pos[0]
        y = pos[1]
        match type :
            case PIECE_TYPE.PAWN    : self.grid[x][y] = Pawn(pos, color, self)
            case PIECE_TYPE.KNIGHT  : self.grid[x][y] = Knight(pos, color, self)
            case PIECE_TYPE.ROOK    : self.grid[x][y] = Rook(pos, color, self)
            case PIECE_TYPE.BISHOP  : self.grid[x][y] = Bishop(pos, color, self)
            case PIECE_TYPE.KING    : self.grid[x][y] = King(pos, color, self)
            case PIECE_TYPE.QUEEN   : self.grid[x][y] = Queen(pos, color, self)
            
    def calculate_all_moves(self) :
        self.square_reached[PIECE_COLOR.WHITE] = self.check_square_reached(PIECE_COLOR.WHITE)
        self.square_reached[PIECE_COLOR.BLACK] = self.check_square_reached(PIECE_COLOR.BLACK)
        
    def calculate_legal_moves(self, color : PIECE_COLOR) :
        self.possible_moves[color] = self.check_possible_moves(color)
        
    def check_square_reached(self, color : PIECE_COLOR) -> list:
        possible_moves = []
        for i in range(8) :
            for j in range(8) :
                piece = self.grid[i][j]
                if (piece == None) : continue
                if (piece.get_color() != color) : continue
                
                moves = piece.check_moves()
                possible_moves += moves
        return possible_moves
                
    def check_possible_moves(self, color : PIECE_COLOR) -> list :
        possible_moves = []
     
        for i in range(8) :
            for j in range(8) :
                piece = self.grid[i][j]
                if (piece == None) : continue
                moves = piece.check_moves()
                if (not self.is_false_board) : moves = self.remove_illegal_moves(piece, moves, color)
                if (piece.get_color() == color) : possible_moves += moves
        return possible_moves
                
        
    def get_number_possible_moves(self, color : PIECE_COLOR) -> int : return len(self.possible_moves[color])
    
    
    def update_piece_last_pos(self, color : PIECE_COLOR) :
        for i in range(8) :
            for j in range(8) :
             

                piece = self.grid[i][j]
                if (piece == None) : continue
                if (piece.get_color() != color) : continue
                
                piece.set_last_pos()
    def get_piece(self, pos :list):
        w_pos = wrap_pos(pos)
        return self.grid[int(w_pos[0])][int(w_pos[1])]
    
    
    def move_piece(self, from_pos : list[int], to_pos : list[int], real_move : bool = True) :
    
        special_move = {"type" : SPECIAL_MOVES.NONE}
        new_x = to_pos[0]
        new_y = to_pos[1]
                
        if (not self.cell_empty(to_pos)) : 
            self.piece_captured(to_pos)
            
        piece = self.get_piece(from_pos)
        self.remove_piece(from_pos)
        

        # EN PASSANT
        if (piece.get_type() == PIECE_TYPE.PAWN) :
            if array_equal(to_pos,piece.en_passant) :
                pawn_affected = [to_pos[0], to_pos[1] - piece.forward]
                self.piece_captured(pawn_affected)
                
                special_move["type"]           = SPECIAL_MOVES.EN_PASSANT
                special_move["captured_pawn_pos"] = pawn_affected
                
                
        #CASTLE 
        elif (piece.get_type() == PIECE_TYPE.KING) :
            king_pos = piece.get_pos()
            
            
            if (array_equal(to_pos, piece.right_castle)) :

                
                rook_affected = [king_pos[0]+3, king_pos[1]]
                new_rook_pos  = [king_pos[0]+1, king_pos[1]]
               
                self.move_piece(rook_affected, new_rook_pos, False)
                
                special_move["type"]        = SPECIAL_MOVES.CASTLE
                special_move["rook_from"]   = rook_affected
                special_move["rook_to"]     = new_rook_pos
        
                
            if (array_equal(to_pos, piece.left_castle)) :
                
                rook_affected = [king_pos[0]-4,king_pos[1]]
                new_rook_pos  = [king_pos[0]-1,king_pos[1]]
                self.move_piece(rook_affected, new_rook_pos, False)
                
                                
                special_move["type"]        = SPECIAL_MOVES.CASTLE
                special_move["rook_from"]   = rook_affected
                special_move["rook_to"]     = new_rook_pos
        #PROMOTION    
        
        if ((new_y == 0) or (new_y == 7)) and (piece.get_type() == PIECE_TYPE.PAWN) :
            
            self.add_piece(PIECE_TYPE.QUEEN, piece.get_color(), to_pos)
            
            special_move["type"]        = SPECIAL_MOVES.PROMOTION
            special_move["pawn_pos"]    = from_pos
        else :
            self.grid[int(new_x)][int(new_y)] = piece
            self.grid[int(new_x)][int(new_y)].set_pos(to_pos)
            self.grid[int(new_x)][int(new_y)].set_moved()
            
            
    
        if (real_move) : 
            self.next_turn()
            return special_move
        
        
        
    def remove_piece(self, pos : list[int]) :
        self.grid[int(pos[0])][int(pos[1])] = None
        
    def piece_captured(self, pos :list[int]) :

        piece = self.get_piece(pos)
        if (not self.is_false_board) :
            if piece.get_color() == PIECE_COLOR.WHITE : self.captured_pieces["white"][piece.get_name()]+=1
            else : self.captured_pieces["black"][piece.get_name()]+=1
        self.remove_piece(pos)
        
    
    def is_checked(self, color : PIECE_COLOR) :
        possible_enemy_move = self.square_reached[not color]
        
        #FIND KING COORDINATES
        king_coord = []
        for i in range(8) :
            for j in range(8) :
                piece = self.grid[i][j]
                if (piece == None) : continue
                if (piece.get_color() != color) : continue
                
                if (piece.get_type() == PIECE_TYPE.KING) :
                    king_coord = [i, j]
                    break
        
        #CHECK IF ONE OF POSSIBLE ENEMY MOVE HIT COORDINATES
        for move in possible_enemy_move :
            if array_equal(move, king_coord) : 
                return True
        return False
    
    def get_board_data(self) :
        data = {'turn' : self.turn, 'captured_pieces' : self.captured_pieces, 'number_of_turn' : self.number_of_turn}
        board_data = [["" for i in range(8)] for j in range(8)]
        for i in range(8) :
            for j in range(8) :
                piece = self.grid[i][j]
                if (piece == None) : continue
                
                board_data[i][j] = piece.get_data()
        data['board'] = board_data
        
        return data
    
    def load_board_data(self, data : dict) :
        self.grid = [[None for i in range(8)] for j in range(8)]
        self.captured_pieces = data['captured_pieces']
        self.turn            = data['turn']
        self.number_of_turn       = data['number_of_turn']
        
        
        board_data      = data['board']
        for i in range(8) :
            for j in range(8) :
                piece = board_data[i][j]
                if (piece == '') : continue
                
                piece_data  = piece.split(';')
                piece_type  = piece_data[0]
                piece_color = piece_data[1]
                piece_moved = piece_data[2]
                self.add_piece(int(piece_type), int(piece_color), [i,j])
                self.grid[i][j].set_moved(piece_moved)
    
    def is_checked_after_move(self, from_pos : list[int], to_pos : list[int], color : PIECE_COLOR) : # HEAVY !!
        # CREATE A FALSE BOARD MAKE THE POSSIBLE MOVE ON FAKE BOARD AND RETURN IF KING IS STILL CHECKED ON FALSE BOARD
        real_board_data = self.get_board_data()
        fake_board      = Chess_board()
        fake_board.load_board_data(real_board_data)
        fake_board.is_false_board = True
        
        if self.get_piece(from_pos) == None : return
        fake_board.move_piece(from_pos, to_pos)
        
        
      
        return fake_board.is_checked(color)
    
    def remove_illegal_moves(self, piece, possible_moves : list[list[int]], color : PIECE_COLOR) :
        clean_moves = []
        piece_color = piece.get_color()
        piece_pos   = piece.get_pos()
        if (piece_color == color) :
            for move in possible_moves :
                if (self.is_checked_after_move(piece_pos, move, piece_color)) : continue
                else :  clean_moves.append(move)
        else :
            clean_moves = possible_moves
        
        return clean_moves         
    
    def check_move_valid(self, from_pos : list[int], to_pos : list[int]) :
       
        piece = self.get_piece(from_pos)
        moves = piece.get_moves()
        

        moves = self.remove_illegal_moves(piece, moves, piece.get_color())

        for move in moves :
            if (array_equal(move, to_pos)) : return True
        return False
        
    
    def cell_safe(self, pos : list[int], color : PIECE_COLOR) :
        possible_enemy_move = self.square_reached[not color]

        # CHECK IF ONE OF POSSIBLE ENEMY MOVE HIT COORDINATES
        for move in possible_enemy_move :
            if (array_equal(move, pos)) : return False
        
        return True
    def cell_empty(self, pos) :
        if (pos[1] > 7) or (pos[1] < 0) : return False
        
        w_pos = wrap_pos(pos)
        return self.grid[int(w_pos[0])][int(w_pos[1])] == None
    
    
    def next_turn(self) :
        self.number_of_turn+=1
        self.turn = not self.turn
        self.update_piece_last_pos(self.turn)
        self.calculate_all_moves()
        if (not self.is_false_board) : self.calculate_legal_moves(self.turn)
        
        # VERIFY CHECKMATE
        if (self.is_checked(self.turn)) :
            
            if (not self.is_false_board) :
                number_of_moves = self.get_number_possible_moves(self.turn)
                if (number_of_moves <= 0) :
                    self.game_ended = True
                    self.winner = not self.turn
        else :
            # STALEMATE
            if (not self.is_false_board) :
                number_of_moves = self.get_number_possible_moves(self.turn)
                if (number_of_moves <= 0) :
                    self.game_ended = True
                    self.winner = None
                    
    def get_board_string(self) :
        board_string = ""
        for i in range(8) :
            for j in range(8) :
                piece = self.grid[j][i]
                if (piece == None) : board_string += "*"
                else : board_string += piece.get_string()
        return board_string
        
            
    def __str__(self):
        board_string = ""
        for i in range(8) :
            for j in range(8) :
                piece = self.grid[j][i]
                if (piece == None) : board_string += "*"
                else : board_string += piece.get_string()
            board_string+="\n"
        return board_string