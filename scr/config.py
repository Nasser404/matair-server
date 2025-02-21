from enum import IntEnum
import random
SERVER_PORT         = 29920
ORB_CODE_LENGHT     = 4


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
    
class CLIENT_TYPE(IntEnum) :
    ORB     = 0
    PLAYER  = 1
    VIEWER  = 2


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


def id_generator(size=4, chars="ABCDEFHIJKLMNOPQRSTUVWXYZ1234567890"):
    return ''.join(random.choice(chars) for _ in range(size))

def remove_client(client : dict, list : list) -> list :
    return [d for d in list if d.get('id') != client['id']]

def wrap_pos(pos) :
    min = 0
    max = 7
    range = max - min + 1
    return[(((pos[0] - min) % range) + range) % range + min, pos[1]]
