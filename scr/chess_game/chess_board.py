from scr.chess_game.piece.piece_type    import Piece
from scr.chess_game.piece.pawn          import Pawn
from scr.chess_game.piece.knight        import Knight
from scr.chess_game.piece.bishop        import Bishop
from scr.chess_game.piece.rook          import Rook
from scr.chess_game.piece.queen         import Queen
from scr.chess_game.piece.king          import King
from scr.enums                          import PIECE_COLOR, PIECE_TYPE, SPECIAL_MOVES
from scr.utils                          import wrap_pos
from numpy                              import array_equal

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
        
                
        self.square_reached[PIECE_COLOR.WHITE] = self.get_all_attacked_squares(PIECE_COLOR.WHITE)
        self.square_reached[PIECE_COLOR.BLACK] = self.get_all_attacked_squares(PIECE_COLOR.BLACK)

    def get_grid(self) -> list[list[Piece]]: return self.grid 
    
    def get_piece(self, pos :list) -> Piece :
        w_pos = wrap_pos(pos)
        return self.grid[int(w_pos[0])][int(w_pos[1])]
    
    
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
            
    def remove_piece(self, pos : list[int]) :
        self.grid[int(pos[0])][int(pos[1])] = None        
        
        
    def update_piece_last_pos(self, color : PIECE_COLOR) :
        for i in range(8) :
            for j in range(8) :
             

                piece = self.grid[i][j]
                if (piece == None) : continue
                if (piece.get_color() != color) : continue
                
                piece.set_last_pos()
    
    
    def piece_captured(self, pos: list[int], is_temporary_move: bool = False):
        piece = self.get_piece(pos)
        if not is_temporary_move :
            color_key = "white" if piece.get_color() == PIECE_COLOR.WHITE else "black"
            self.captured_pieces[color_key][piece.get_name()] += 1
        self.remove_piece(pos)
        
    def find_king_pos(self, color : PIECE_COLOR) -> list[int] :
        for i in range(8) :
            for j in range(8) :
                piece = self.grid[i][j]
                
                if piece is None or piece.get_color() != color:
                    continue
        
                if (piece.get_type() == PIECE_TYPE.KING) :
                    return [i, j]
                      
        return None        
    
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
    
    
    def get_legal_moves(self, color: PIECE_COLOR) -> list:
        """
        Generates a list of all legal moves for a given color.
        A move is legal if it is a valid move for the piece and does not
        leave the player's own king in check.
        """
        legal_moves = []
        for i in range(8):
            for j in range(8):
                piece = self.grid[i][j]
                if piece is None or piece.get_color() != color:
                    continue

                # Get all potential moves for this piece
                pseudo_legal_moves = piece.check_moves()

                # Filter out moves that would leave the king in check
                for move in pseudo_legal_moves:
                    if not self.is_checked_after_move(piece.get_pos(), move, color):
                        legal_moves.append(move) # Or better, store as (from_pos, to_pos)

        return legal_moves

        
    def get_all_attacked_squares(self, color: PIECE_COLOR) -> list:
        """
        Generates a list of all squares attacked by a given color.
        """
        attacked_squares = []
        for i in range(8):
            for j in range(8):
                piece = self.grid[i][j]
                if piece is None or piece.get_color() != color:
                    continue
                
                # For pawns, attack moves are different from forward moves.
                # This logic might need to be specific within the piece's move generation.
                # For now, we assume check_moves() returns all possible squares.
                moves = piece.check_moves() 
                attacked_squares.extend(moves)
        return attacked_squares
        
    
    def move_piece(self, from_pos: list[int], to_pos: list[int], real_move: bool = True) -> dict:
        
        # This dictionary will hold all information needed to undo the move.
        move_info = {
            "from_pos": from_pos,
            "to_pos": to_pos,
            "captured_piece": None,
            "special_move": {"type": SPECIAL_MOVES.NONE}
        }

        piece = self.get_piece(from_pos)
        if piece is None: return # Should not happen with valid moves

        # --- Capture critical 'before' state ---
        move_info["was_moved"] = piece.has_moved # Capture status BEFORE moving

        # --- Execute the move ---
        
        # Is a piece being captured?
        captured_piece = self.get_piece(to_pos)
        if captured_piece:
            move_info["captured_piece"] = captured_piece
            # The piece_captured method updates the count, which we'll need to reverse
            self.piece_captured(to_pos, is_temporary_move=not real_move)
        
        # Move the piece in the grid
        self.grid[int(to_pos[0])][int(to_pos[1])] = piece
        self.remove_piece(from_pos)
        piece.set_pos(to_pos)

        # --- Handle Special Moves ---
        
        # EN PASSANT
        if piece.get_type() == PIECE_TYPE.PAWN and array_equal(to_pos, piece.en_passant):
            pawn_affected_pos = [to_pos[0], to_pos[1] - piece.forward]
            # We need to explicitly get the captured pawn here, because it's not at to_pos
            move_info["captured_piece"] = self.get_piece(pawn_affected_pos)
            self.piece_captured(pawn_affected_pos, is_temporary_move=not real_move)
            
            move_info["special_move"]["type"] = SPECIAL_MOVES.EN_PASSANT
            move_info["special_move"]["captured_pawn_pos"] = pawn_affected_pos

        # CASTLE
        elif piece.get_type() == PIECE_TYPE.KING:
            king_pos = piece.get_pos()
            if array_equal(to_pos, piece.right_castle):
                rook_from = [king_pos[0] + 3, king_pos[1]]
                rook_to = [king_pos[0] + 1, king_pos[1]]
                self.move_piece(rook_from, rook_to, False) # Recursive call is fine for this
                
                move_info["special_move"] = {"type": SPECIAL_MOVES.CASTLE, "rook_from": rook_from, "rook_to": rook_to}
            if array_equal(to_pos, piece.left_castle):
                rook_from = [king_pos[0] - 4, king_pos[1]]
                rook_to = [king_pos[0] - 1, king_pos[1]]
                self.move_piece(rook_from, rook_to, False) # Recursive call is fine for this
                
                move_info["special_move"] = {"type": SPECIAL_MOVES.CASTLE, "rook_from": rook_from, "rook_to": rook_to}
          

        # PROMOTION
        if (to_pos[1] == 0 or to_pos[1] == 7) and piece.get_type() == PIECE_TYPE.PAWN:
            self.add_piece(PIECE_TYPE.QUEEN, piece.get_color(), to_pos)
            move_info["special_move"] = {"type": SPECIAL_MOVES.PROMOTION, "pawn_pos": to_pos}
            # The original piece is now gone, so we need to save it for the undo
            move_info["promoted_from_pawn"] = piece 

        else:
            # Standard move completion
            piece.set_moved()

        # If it's a real move, proceed to the next turn. Otherwise, just return the undo info.
        if real_move:
            self.next_turn()
        
        return move_info
        
    def unmake_move(self, undo_info: dict):
        from_pos = undo_info["from_pos"]
        to_pos = undo_info["to_pos"]

        # Get the piece that moved
        moving_piece = self.get_piece(to_pos)

        # --- Reverse Promotion ---
        if undo_info["special_move"]["type"] == SPECIAL_MOVES.PROMOTION:
            # The piece at to_pos is a Queen, replace it with the original pawn
            pawn = undo_info["promoted_from_pawn"]
            self.grid[int(to_pos[0])][int(to_pos[1])] = pawn
            moving_piece = pawn 

        # --- Move the piece back to its original square ---
        self.grid[int(from_pos[0])][int(from_pos[1])] = moving_piece
        moving_piece.set_pos(from_pos)
        self.grid[int(to_pos[0])][int(to_pos[1])] = None 

        # --- Restore moved status ---
        if not undo_info["was_moved"]:
            moving_piece.set_moved(False) 

        # --- Put back any captured piece ---
        captured_piece = undo_info["captured_piece"]
        if captured_piece:
            capture_pos = to_pos # Default capture position
            
            if undo_info["special_move"]["type"] == SPECIAL_MOVES.EN_PASSANT:
                capture_pos = undo_info["special_move"]["captured_pawn_pos"]
            
            self.grid[int(capture_pos[0])][int(capture_pos[1])] = captured_piece
            
            # We also need to decrement the captured pieces count if it was incremented
            color_key = "white" if captured_piece.get_color() == PIECE_COLOR.WHITE else "black"
            self.captured_pieces[color_key][captured_piece.get_name()] -= 1

        # --- Undo Castling's rook move ---
        if undo_info["special_move"]["type"] == SPECIAL_MOVES.CASTLE:
            rook_from = undo_info["special_move"]["rook_from"]
            rook_to = undo_info["special_move"]["rook_to"]
            rook = self.get_piece(rook_to)
            
            self.grid[int(rook_from[0])][int(rook_from[1])] = rook
            rook.set_pos(rook_from)
            self.grid[int(rook_to[0])][int(rook_to[1])] = None
            rook.set_moved(False) # The rook had not moved before a castle    
        
  
    
    def is_checked(self, color: PIECE_COLOR):

        enemy_attacks = self.square_reached[not color]
        
        # FIND KING COORDINATES
        king_coord = self.find_king_pos(color) 
        if king_coord is None: return False
        
        # CHECK IF ONE OF POSSIBLE ENEMY MOVE HIT COORDINATES
        for move in enemy_attacks:
            if array_equal(move, king_coord):
                return True
        return False
    
 
    def is_checked_after_move(self, from_pos: list[int], to_pos: list[int], color: PIECE_COLOR) -> bool:
        # 1. Make the move and get the undo information
        undo_info = self.move_piece(from_pos, to_pos, real_move=False)

        # 2. Check if the king is now in check
        self.square_reached[not color] = self.get_all_attacked_squares(not color)
        is_in_check = self.is_checked(color) 

        # 3. Unmake the move
        self.unmake_move(undo_info)
        
        # 4. restore the opponent's attack map to its previous state
        self.square_reached[not color] = self.get_all_attacked_squares(not color)

        return is_in_check

    
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
        
    
    
    
    
    def next_turn(self):
        self.number_of_turn += 1
        self.turn = not self.turn
        self.update_piece_last_pos(self.turn)
        

        # Calculate and store the legal moves for the current player.
        self.possible_moves[self.turn] = self.get_legal_moves(self.turn)

        # Update the list of squares the opponent attacks for check detection.
        self.square_reached[not self.turn] = self.get_all_attacked_squares(not self.turn)
        
        # VERIFY CHECKMATE / STALEMATE
        is_in_check = self.is_checked(self.turn)
        
        if len(self.possible_moves[self.turn]) == 0:
            self.game_ended = True
            
            if is_in_check:
                self.winner = not self.turn # Checkmate
            else:
                self.winner = None # Stalemate
            
    
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
        self.number_of_turn  = data['number_of_turn']
        board_data           = data['board']
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