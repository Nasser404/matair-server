from .piece_type import Piece
from scr.config import PIECE_COLOR, PIECE_TYPE, wrap_pos
class Pawn(Piece) :
    def __init__(self, pos, color, board):
        super().__init__("Pawn", pos, PIECE_TYPE.PAWN, color, board)
        self.en_passant = [-1, -1]
        self.string = "P" if color == PIECE_COLOR.BLACK else "p"
    
    def check_moves(self) :
        self.moves = []
        
        x = self.pos[0]
        y = self.pos[1]
        
        # simple forward
        if (self.cell_empty([x, y + self.forward])) : self.add_move([x, y + self.forward])
        #double forward
        if (not self.has_moved) and (self.cell_empty([x, y + 2*self.forward])) : self.add_move([x, y + 2*self.forward])
        
        # eat left
        if (not self.cell_empty([x+1, y + self.forward])) : 
            if (not self.on_team([x+1, y + self.forward])) : self.add_move([x+1, y + self.forward])
            
        # eat right
        if (not self.cell_empty([x-1, y + self.forward])) : 
            if (not self.on_team([x-1, y + self.forward])) : self.add_move([x-1, y + self.forward])
        
        # en passant left
        
        if (not self.cell_empty([x + 1, y])) :
            piece = self.get_piece([x + 1, y])
            if (piece.get_color() != self.color) :
                if (piece.get_type() == PIECE_TYPE.PAWN) :
                    if (piece.get_pos()[1] == piece.get_last_pos()[1] + 2 * piece.forward) :
                        self.add_move([x + 1, y + self.forward])
                        self.en_passant = wrap_pos([x + 1, y + self.forward])
        
        # en passant left
        if (not self.cell_empty([x - 1, y])) :
            piece = self.get_piece([x - 1, y])
            if (piece.get_color() != self.color) :
                if (piece.get_type() == PIECE_TYPE.PAWN) :
                    if (piece.get_pos()[1] == piece.get_last_pos()[1] + 2 * piece.forward) :
                        self.add_move([x - 1, y + self.forward])
                        self.en_passant = wrap_pos([x - 1, y + self.forward])
        return self.moves