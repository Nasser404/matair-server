from scr.chess_game.piece.piece_type    import Piece
from scr.enums                          import PIECE_COLOR, PIECE_TYPE
from scr.utils                          import wrap_pos

class Rook(Piece) :
    def __init__(self, pos, color, board):
        super().__init__("Rook", pos, PIECE_TYPE.ROOK, color, board)
        self.string = "R" if color == PIECE_COLOR.BLACK else "r"
        
        
    def check_moves(self) :
        self.moves = []
    
        x = self.pos[0]
        y = self.pos[1]
        
        # RIGHT
        i = 1
        while(self.cell_empty( [x+i, y])) :
            self.add_move([x+i, y])
            i+=1
        if (not self.on_team( [x+i, y])) : self.add_move([x+i, y])
        
        #LEFT
        i = -1
        while(self.cell_empty( [x+i, y])) :
            self.add_move([x+i, y])
            i-=1
        if (not self.on_team([x+i, y])) : self.add_move([x+i, y])
        #UP
        i = self.forward
        while(self.cell_empty( [x, y+i])) :
            self.add_move([x, y+i])
            i+=self.forward
        if (not self.on_team( [x, y+i])) : self.add_move([x, y+i])
        
        #DOWN
        i = -self.forward
        while(self.cell_empty( [x, y+i])) :
            self.add_move([x, y+i])
            i-=self.forward
        if (not self.on_team( [x, y+i])) : self.add_move([x, y+i])   
        
        
        return self.moves