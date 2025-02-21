from scr.config import PIECE_COLOR, wrap_pos

class Piece() :
    def __init__(self, name, pos, type, color, board):
        self.name           = name
        self.pos            = pos
        self.type           = type
        self.color          = color
        self.my_board       = board
        self.moves          = []
        self.has_moved      = False
        self.last_pos       = [-1, -1]
        self.special_moves  = []
        self.forward        = -1 if color == PIECE_COLOR.WHITE else 1
    
    def get_data(self) : return f"{self.type};{self.color};{self.has_moved}"     
    
    def get_name(self) : return self.name
    def get_pos(self)  : return self.pos
    def get_last_pos(self) : return self.last_pos
    def get_type(self) : return self.type
    def get_color(self) : return self.color
    def get_moves(self) : return self.moves
    
    def set_moved(self) : self.has_moved = True
    def set_last_pos(self) :self.last_pos = self.pos
    def set_pos(self, new_pos) :
        self.set_last_pos()
        self.last_pos = new_pos
    
    
    def add_move(self, move) :
        if not (move == self.pos) : self.moves.append(move)
    
    def on_team(self, pos) :
        if (0 < pos[1] < 7) : return True
        grid = self.my_board.get_grid()
        
        if self.cell_empty(pos) : return False
        
        w_pos = wrap_pos(pos)
        return grid[w_pos[0], w_pos[1]].color == self.color
    
    def cell_empty(self, pos) :
        if (0 < pos[1] < 7) : return False
        w_pos = wrap_pos(pos)
        grid = self.my_board.get_grid()
        return grid[w_pos[0], w_pos[1]] == None
        
    def get_piece(self, pos) :
        if (0 < pos[1] < 7)     : return None
        if self.cell_empty(pos) : return None
        
        grid = self.my_board.get_grid()
        w_pos = wrap_pos(pos)
        return grid[w_pos[0]][w_pos[1]]
    
    def get_string(self) : return self.string
        
        
        
        
        