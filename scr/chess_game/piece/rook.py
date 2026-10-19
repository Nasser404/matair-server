from scr.chess_game.piece.piece_type    import Piece, ORTHOGONAL
from scr.enums                          import PieceType


class Rook(Piece):
    name   = "Rook"
    symbol = "r"
    type   = PieceType.ROOK

    def check_moves(self):
        return self._slide(ORTHOGONAL)
