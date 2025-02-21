from .piece_type import Piece
from scr.config import PIECE_COLOR, PIECE_TYPE
class Bishop(Piece) :
    def __init__(self, pos, color, board):
        super().__init__("Bishop", pos, PIECE_TYPE.BISHOP, color, board)
        self.string = "B" if color == PIECE_COLOR.BLACK else "b"
        
        
    def check_moves(self) :
        self.moves = []
    
        x = self.pos[0]
        y = self.pos[1]
        
        #Diag right up
        i = 1
        j = self.forward
        while(self.cell_empty( [x+i, y+j])) :
            self.add_move([x+i, y+j])
            i+=1
            j+=self.forward
        if (not self.on_team( [x+i, y+j])) : self.add_move([x+i, y+j])
        
        #Diag left up
        i = -1
        j = self.forward
        while(self.cell_empty( [x+i, y+j])) :
            self.add_move([x+i, y+j])
            i-=1
            j+=self.forward
        if (not self.on_team( [x+i, y+j])) : self.add_move([x+i, y+j])
        
        #Diag right down
        i = 1
        j = -self.forward
        while(self.cell_empty( [x+i, y+j])) :
            self.add_move([x+i, y+j])
            i+=1
            j-=self.forward
        if (not self.on_team( [x+i, y+j])) : self.add_move([x+i, y+j])
        
        #Diag left down
        i = -1
        j = -self.forward
        while(self.cell_empty( [x+i, y+j])) :
            self.add_move([x+i, y+j])
            i-=1
            j-=self.forward
        if (not self.on_team( [x+i, y+j])) : self.add_move([x+i, y+j])
        return self.moves