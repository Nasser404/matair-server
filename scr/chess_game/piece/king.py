from scr.chess_game.piece.piece_type    import Piece, ALL_DIRECTIONS
from scr.enums                          import PieceType


class King(Piece):
    name   = "King"
    symbol = "k"
    type   = PieceType.KING

    # Castling is disabled on the cylinder board.
    def check_moves(self):
        return self._jump(ALL_DIRECTIONS)
