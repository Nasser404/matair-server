"""Enums shared with the ESP32 orb and the GameMaker client.

These numbers ARE the wire protocol: never renumber or reuse a value.
"""
from enum import IntEnum


class MessageType(IntEnum):
    IDENTIFICATION          = 0

    PING                    = 1
    PONG                    = 2

    GAME_DATA               = 3
    GAME_INFO               = 4
    GAME_DISCONNECT         = 5   # unused

    ORB_DATA                = 6
    ORB_RESET               = 7

    ORB_CONNECT             = 8
    PLAYER_CONNECT          = 9
    VIEWER_CONNECT          = 10

    ORB_LIST                = 11
    GAME_LIST               = 12

    DISCONNECT_REASON       = 13

    ASK_MOVE                = 14
    MOVE                    = 15

    ORB_NEW_GAME            = 16
    ORB_CONTINUE_GAME       = 17
    ORB_END_GAME            = 18

    DISCONNECT_FROM_SERVER  = 19
    INFORMATION             = 20

    GAME_CHAT               = 21


class ClientType(IntEnum):
    ORB     = 0
    PLAYER  = 1
    VIEWER  = 2


class InformationType(IntEnum):
    ORB_NOT_READY   = 0
    MOVE_NOT_LEGAL  = 1
    NOT_PLAYER_TURN = 2
    NOT_GAME_PLAYER = 3


class DisconnectReason(IntEnum):
    NO_REASON           = 0
    INVALID_ORB_CODE    = 1
    TIMEOUT             = 2   # unused by the server
    ORB_DISCONNECTED    = 3
    SILENT              = 4   # unused by the server
    GAME_NOT_JOINABLE   = 5


class OrbStatus(IntEnum):
    IDLE        = 0
    OCCUPIED    = 1   # physically moving pieces


class PieceType(IntEnum):
    PAWN    = 0
    KNIGHT  = 1
    ROOK    = 2
    BISHOP  = 3
    KING    = 4
    QUEEN   = 5


class PieceColor(IntEnum):
    WHITE = 0
    BLACK = 1


class SpecialMove(IntEnum):
    PROMOTION   = 0
    EN_PASSANT  = 1   # disabled rule, value kept for the protocol
    CASTLE      = 2   # disabled rule, value kept for the protocol
    NONE        = 3
