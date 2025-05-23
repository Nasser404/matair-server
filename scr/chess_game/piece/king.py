from scr.chess_game.piece.piece_type    import Piece
from scr.enums                          import PIECE_COLOR, PIECE_TYPE
from scr.utils                          import wrap_pos

class King(Piece) :
    def __init__(self, pos, color, board):
        super().__init__("King", pos, PIECE_TYPE.KING, color, board)
        self.string = "K" if color == PIECE_COLOR.BLACK else "k"
        self.right_castle = [-1, -1]
        self.left_castle  = [-1, -1]
        
    def check_moves(self) :
        self.moves = []
        
        x = self.pos[0]
        y = self.pos[1]
        
        possible_moves = [
        [x + 1, y], [x - 1, y], [x, y+self.forward], [x, y-self.forward],
        [x+1, y+self.forward], [x+1, y-self.forward], [x-1, y +self.forward], [x-1, y-self.forward],
        ] 
        
        for square in possible_moves :
            if (not self.on_team(square)) : self.add_move(square)
            
        # Right castle (DISABELED)
        if (False) : #not self.has_moved 
            rook = self.get_piece([x + 3, y])
            if rook != None :
                if ((not rook.has_moved) and (rook.get_type() == PIECE_TYPE.ROOK)) :
                    row_clear = self.cell_empty([x+1, y]) and self.cell_empty([x+2, y])
                    row_safe  = self.my_board.cell_safe([x + 1, y], self.color) and self.my_board.cell_safe([x + 2, y], self.color)
                    if row_clear and row_safe :
                        self.add_move([x+2, y])
                        self.right_castle = [x+2, y]
        
        #Left castle # DISABELED
        if (False) : #not self.has_moved 
            rook = self.get_piece([x - 4, y])
            if rook != None :
                if ((not rook.has_moved) and (rook.get_type() == PIECE_TYPE.ROOK)) :
                    row_clear = self.cell_empty([x-1, y]) and self.cell_empty([x-2, y]) and self.cell_empty([x-3, y])
                    row_safe  = self.my_board.cell_safe([x - 1, y], self.color) and self.my_board.cell_safe([x - 2, y], self.color) and self.my_board.cell_safe([x - 3, y], self.color)
                    if row_clear and row_safe :
                        self.add_move([x-2, y])
                        self.right_castle = [x-2, y]
        return self.moves