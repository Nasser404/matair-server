from scr.chess_game.piece.piece_type    import Piece
from scr.chess_game.piece.pawn          import Pawn
from scr.chess_game.piece.knight        import Knight
from scr.chess_game.piece.bishop        import Bishop
from scr.chess_game.piece.rook          import Rook
from scr.chess_game.piece.queen         import Queen
from scr.chess_game.piece.king          import King
from scr.enums                          import PieceColor, PieceType, SpecialMove

PIECE_CLASSES = {
    PieceType.PAWN   : Pawn,
    PieceType.KNIGHT : Knight,
    PieceType.ROOK   : Rook,
    PieceType.BISHOP : Bishop,
    PieceType.KING   : King,
    PieceType.QUEEN  : Queen,
}
BACK_RANK = (PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
             PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK)


def empty_capture_count() -> dict:
    return {"Pawn": 0, "Rook": 0, "Knight": 0, "Bishop": 0, "Queen": 0, "King": 0}


class ChessBoard:
    """Cylinder chess. grid[x][y]: x is the column (it wraps: the a-file touches the h-file),
    y is the row (it doesn't wrap). Black starts on rows 0-1, white on rows 6-7.
    En passant and castling are disabled."""

    def __init__(self):
        self.grid: list[list[Piece | None]] = [[None] * 8 for _ in range(8)]
        self.captured_pieces = {"white": empty_capture_count(), "black": empty_capture_count()}
        self.turn            = PieceColor.WHITE     # a bool after the first move, sent to clients as-is
        self.number_of_turn  = 0
        self.game_ended      = False
        self.winner          = None

        for x, piece_type in enumerate(BACK_RANK):
            self.add_piece(piece_type,     PieceColor.BLACK, [x, 0])
            self.add_piece(PieceType.PAWN, PieceColor.BLACK, [x, 1])
            self.add_piece(PieceType.PAWN, PieceColor.WHITE, [x, 6])
            self.add_piece(piece_type,     PieceColor.WHITE, [x, 7])

        self.legal_moves = self.compute_legal_moves(self.turn)

    def add_piece(self, piece_type: PieceType, color: PieceColor, pos: list[int]):
        x, y = pos
        self.grid[x][y] = PIECE_CLASSES[piece_type]([x, y], color, self)

    def pieces(self, color):
        """(x, y, piece) for every piece of `color` on the board."""
        for x in range(8):
            for y in range(8):
                piece = self.grid[x][y]
                if piece is not None and piece.color == color:
                    yield x, y, piece

    # ---------------------------------------------------------------- legality
    def attacked_squares(self, color) -> set[tuple[int, int]]:
        return {(mx, my) for _, _, piece in self.pieces(color) for mx, my in piece.check_moves()}

    def is_in_check(self, color) -> bool:
        king = next(((x, y) for x, y, piece in self.pieces(color) if piece.type == PieceType.KING), None)
        return king is not None and king in self.attacked_squares(not color)

    def leaves_king_safe(self, from_pos, to_pos, color) -> bool:
        """Try the move on the grid, look for check, then put everything back.
        Only the opponent's attacks are computed, and they only depend on which squares are occupied
        and by whom, so the moved piece's own state (position, has_moved, promotion) can stay untouched."""
        (fx, fy), (tx, ty) = from_pos, to_pos
        mover, captured = self.grid[fx][fy], self.grid[tx][ty]
        self.grid[tx][ty], self.grid[fx][fy] = mover, None
        try:
            return not self.is_in_check(color)
        finally:
            self.grid[fx][fy], self.grid[tx][ty] = mover, captured

    def compute_legal_moves(self, color) -> set[tuple[tuple[int, int], tuple[int, int]]]:
        """Every legal ((from_x, from_y), (to_x, to_y)) for `color`."""
        legal = set()
        for x, y, piece in list(self.pieces(color)):
            for tx, ty in piece.check_moves():
                if self.leaves_king_safe((x, y), (tx, ty), color):
                    legal.add(((x, y), (tx, ty)))
        return legal

    def is_move_valid(self, from_pos: list[int], to_pos: list[int]) -> bool:
        """Is this a legal move for the side to move? Columns wrap, rows outside 0..7 are refused."""
        (fx, fy), (tx, ty) = from_pos, to_pos
        if not (0 <= fy <= 7 and 0 <= ty <= 7):
            return False
        return ((fx % 8, fy), (tx % 8, ty)) in self.legal_moves

    # ---------------------------------------------------------------- playing
    def move_piece(self, from_pos: list[int], to_pos: list[int]) -> dict:
        """Play an already validated move, pass the turn and return the special move info for the clients."""
        fx, fy = from_pos[0] % 8, from_pos[1]
        tx, ty = to_pos[0] % 8, to_pos[1]
        piece, captured = self.grid[fx][fy], self.grid[tx][ty]

        if captured is not None:
            color_key = "white" if captured.color == PieceColor.WHITE else "black"
            self.captured_pieces[color_key][captured.name] += 1

        self.grid[fx][fy] = None
        if piece.type == PieceType.PAWN and ty in (0, 7):
            self.add_piece(PieceType.QUEEN, piece.color, [tx, ty])     # promotion, always to a queen
            special_move = {"type": SpecialMove.PROMOTION, "pawn_pos": [tx, ty]}
        else:
            self.grid[tx][ty] = piece
            piece.pos = [tx, ty]
            piece.has_moved = True
            special_move = {"type": SpecialMove.NONE}

        self.next_turn()
        return special_move

    def next_turn(self):
        self.number_of_turn += 1
        self.turn = not self.turn
        self.legal_moves = self.compute_legal_moves(self.turn)

        if not self.legal_moves:
            self.game_ended = True
            self.winner = (not self.turn) if self.is_in_check(self.turn) else None   # checkmate / stalemate

    # ---------------------------------------------------------------- output
    def get_board_data(self) -> dict:
        return {
            'turn'            : self.turn,
            'captured_pieces' : self.captured_pieces,
            'number_of_turn'  : self.number_of_turn,
            'board'           : [["" if piece is None else piece.get_data() for piece in column] for column in self.grid],
        }

    def get_board_string(self) -> str:
        """Row by row (y = 0 first), '*' for an empty square."""
        return "".join("*" if self.grid[x][y] is None else self.grid[x][y].string
                       for y in range(8) for x in range(8))

    def __str__(self):
        board = self.get_board_string()
        return "\n".join(board[i:i + 8] for i in range(0, 64, 8))
