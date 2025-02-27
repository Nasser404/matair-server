from enum import IntEnum

class MESSAGE_TYPE(IntEnum):
    IDENTIFICATION  = 0            
    
    PING            = 1
    PONG            = 2
    
    GAME_DATA       = 3
    GAME_INFO       = 4
    GAME_DISCONNECT = 5
    
    ORB_DATA        = 6
    ORB_RESET       = 7
    
    ORB_CONNECT     = 8
    PLAYER_CONNECT  = 9
    VIEWER_CONNECT  = 10

    ORB_LIST        = 11
    GAME_LIST       = 12
    
    DISCONNECT_REASON=13
    
    ASK_MOVE        = 14
    MOVE            = 15
    
    ORB_NEW_GAME    = 16
    ORB_CONTINUE_GAME=17
    ORB_END_GAME    = 18
    
    DISCONNECT_FROM_SERVER = 19  
    INFORMATION            = 20 
    
    GAME_CHAT              = 21
    
class CLIENT_TYPE(IntEnum) :
    ORB     = 0
    PLAYER  = 1
    VIEWER  = 2

class INFORMATION_TYPE(IntEnum) :
    ORB_NOT_READY     = 0


class DISCONNECT_REASONS(IntEnum) :
    NO_REASON           = 0
    INVALID_ORB_CODE    = 1
    TIMEOUT             = 2
    ORB_DISCONNECTED    = 3
    SILENT              = 4
    GAME_NOT_JOINABLE   = 5
    
class ORB_STATUS(IntEnum) :
    IDLE        = 0
    OCCUPIED    = 1
    

class PIECE_TYPE(IntEnum) :
    PAWN    = 0
    KNIGHT  = 1
    ROOK    = 2
    BISHOP  = 3
    KING    = 4
    QUEEN   = 5


class PIECE_COLOR(IntEnum) :
    WHITE = 0
    BLACK = 1

