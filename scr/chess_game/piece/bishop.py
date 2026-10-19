from scr.chess_game.piece.piece_type    import Piece, DIAGONAL
from scr.enums                          import PieceType


class Bishop(Piece):
    name   = "Bishop"
    symbol = "b"
    type   = PieceType.BISHOP

    def check_moves(self):
        return self._slide(DIAGONAL)
