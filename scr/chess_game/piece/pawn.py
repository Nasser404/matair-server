from scr.chess_game.piece.piece_type    import Piece
from scr.enums                          import PieceType


class Pawn(Piece):
    name   = "Pawn"
    symbol = "p"
    type   = PieceType.PAWN

    def check_moves(self):
        x, y = self.pos
        f = self.forward
        moves = []

        # forward, and two squares on its first move (both squares must be empty)
        if self._is_empty(x, y + f):
            moves.append([x, y + f])
            if not self.has_moved and self._is_empty(x, y + 2 * f):
                moves.append([x, y + 2 * f])

        # diagonal captures, also across the a/h seam
        for dx in (1, -1):
            if self._has_enemy(x + dx, y + f):
                moves.append([(x + dx) % 8, y + f])

        return moves
