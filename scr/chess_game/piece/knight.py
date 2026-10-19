from scr.chess_game.piece.piece_type    import Piece
from scr.enums                          import PieceType

KNIGHT_JUMPS = ((2, 1), (-2, 1), (2, -1), (-2, -1), (1, 2), (-1, 2), (1, -2), (-1, -2))


class Knight(Piece):
    name   = "Knight"
    symbol = "n"
    type   = PieceType.KNIGHT

    def check_moves(self):
        return self._jump(KNIGHT_JUMPS)
