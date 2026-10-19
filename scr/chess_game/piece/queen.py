from scr.chess_game.piece.piece_type    import Piece, ALL_DIRECTIONS
from scr.enums                          import PieceType


class Queen(Piece):
    name   = "Queen"
    symbol = "q"
    type   = PieceType.QUEEN

    def check_moves(self):
        return self._slide(ALL_DIRECTIONS)
