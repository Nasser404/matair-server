from .piece_type import Piece
from scr.config import PIECE_COLOR, PIECE_TYPE, wrap_pos
class Queen(Piece) :
    def __init__(self, pos, color, board):
        super().__init__("Queen", pos, PIECE_TYPE.QUEEN, color, board)
        self.string = "Q" if color == PIECE_COLOR.BLACK else "q"
        
        
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