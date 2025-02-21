from .piece_type import Piece
from scr.config import PIECE_COLOR, PIECE_TYPE
class Knight(Piece) :
    def __init__(self, pos, color, board):
        super().__init__("Knight", pos, PIECE_TYPE.KNIGHT, color, board)
        self.string = "N" if color == PIECE_COLOR.BLACK else "n"
        
        
    def check_moves(self) :
        self.moves = []
        
        x = self.pos[0]
        y = self.pos[1]
        
        possible_moves = [
            [x + 2, y + self.forward], [x - 2, y + self.forward],
            [x + 2, y - self.forward], [x - 2, y - self.forward],
            [x + 1, y + 2 * self.forward], [x - 1, y + 2 * self.forward],
            [x + 1, y - 2 * self.forward], [x - 1, y - 2 * self.forward],
        ] 
        
        for square in possible_moves :
            if (not self.on_team(square)) : self.add_move(square)
        return self.moves