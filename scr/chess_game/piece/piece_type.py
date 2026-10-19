from scr.enums import PieceColor

ORTHOGONAL     = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGONAL       = ((1, 1), (-1, 1), (1, -1), (-1, -1))
ALL_DIRECTIONS = ORTHOGONAL + DIAGONAL


class Piece:
    """A piece on the cylinder board: columns (x) wrap around (the a-file touches the h-file),
    rows (y) stop at the edges."""
    name   = ""     # key in captured_pieces: "Pawn", "Rook", ...
    symbol = ""     # letter in the board string, uppercase for black
    type   = None   # PieceType

    def __init__(self, pos: list[int], color: PieceColor, board):
        self.pos       = pos
        self.color     = color
        self.board     = board
        self.has_moved = False
        self.forward   = -1 if color == PieceColor.WHITE else 1   # white moves towards row 0
        self.string    = self.symbol.upper() if color == PieceColor.BLACK else self.symbol

    def get_data(self) -> str:
        return f"{self.type};{self.color};{int(self.has_moved)}"

    def check_moves(self) -> list[list[int]]:
        """Squares this piece can reach, without checking whether its own king is left in check."""
        raise NotImplementedError

    def _square(self, x: int, y: int):
        """(on_board, piece) for a square. Columns wrap, rows outside 0..7 are off the board."""
        if not 0 <= y <= 7:
            return False, None
        return True, self.board.grid[x % 8][y]

    def _is_empty(self, x: int, y: int) -> bool:
        on_board, piece = self._square(x, y)
        return on_board and piece is None

    def _has_enemy(self, x: int, y: int) -> bool:
        on_board, piece = self._square(x, y)
        return on_board and piece is not None and piece.color != self.color

    def _jump(self, offsets) -> list[list[int]]:
        """King and knight: every offset landing on an empty or enemy square."""
        x, y = self.pos
        return [[(x + dx) % 8, y + dy] for dx, dy in offsets
                if self._is_empty(x + dx, y + dy) or self._has_enemy(x + dx, y + dy)]

    def _slide(self, directions) -> list[list[int]]:
        """Rook, bishop and queen: go in each direction until blocked, capturing an enemy piece."""
        x, y = self.pos
        moves = []
        for dx, dy in directions:
            for step in range(1, 8):    # at most 7 steps: an 8th would come back to our own square
                tx, ty = x + dx * step, y + dy * step
                on_board, piece = self._square(tx, ty)
                if not on_board:
                    break
                if piece is None or piece.color != self.color:
                    moves.append([tx % 8, ty])
                if piece is not None:
                    break
        return moves

    def __str__(self):
        return self.name
