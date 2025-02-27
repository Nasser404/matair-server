from scr.enums      import PIECE_COLOR
from scr.utils      import wrap_pos
from numpy          import array_equal

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
    
    def get_data(self) : return f"{self.type};{self.color};{int(self.has_moved)}"     
    
    def get_name(self) : return self.name
    def get_pos(self)  : return self.pos
    def get_last_pos(self) : return self.last_pos
    def get_type(self) : return self.type
    def get_color(self) : return self.color
    def get_moves(self) : return self.moves
    
    def set_moved(self, moved = True) : self.has_moved = moved
    def set_last_pos(self) :self.last_pos = self.pos
    def set_pos(self, new_pos) :
        self.set_last_pos()
        self.pos = new_pos
    
    
    def add_move(self, move) :
        if (not array_equal(move, self.pos)) : self.moves.append(wrap_pos(move))
    
    def on_team(self, pos) :
        if (pos[1] > 7) or (pos[1] < 0)  : return True
        
        grid = self.my_board.get_grid()
        if self.cell_empty(pos) : return False
        
        w_pos = wrap_pos(pos)
        return (grid[w_pos[0]][w_pos[1]].get_color() == self.color)
    
    def cell_empty(self, pos) :
        if (pos[1] > 7) or (pos[1] < 0)  : return False
        w_pos = wrap_pos(pos)
        grid = self.my_board.get_grid()
        return (grid[w_pos[0]][w_pos[1]] == None)
        
    def get_piece(self, pos) :
        if (pos[1] > 7) or (pos[1] < 0)      : return None
        if self.cell_empty(pos) : return None
        
        grid = self.my_board.get_grid()
        w_pos = wrap_pos(pos)
        return grid[w_pos[0]][w_pos[1]]
    
    def get_string(self) : return self.string
    
    def __str__(self):
        return self.name
        
        
        
        
        