from .piece_type import Piece
from scr.config import PIECE_COLOR, PIECE_TYPE, wrap_pos
class Rook(Piece) :
    def __init__(self, pos, color, board):
        super().__init__("Rook", pos, PIECE_TYPE.ROOK, color, board)