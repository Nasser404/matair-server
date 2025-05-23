from random import choice

def id_generator(size : int = 4, chars : str="ABCDEFHIJKLMNOPQRSTUWXYZ1234567890") -> str :
    # generate a random id
    return ''.join(choice(chars) for _ in range(size))

def remove_client(client : dict, list : list) -> list :
    # filter (remove) and return the list based on given client id
    return [d for d in list if d.get('id') != client['id']]

def wrap_pos(pos : list) -> list:
    min = 0
    max = 7
    range = max - min + 1
    return[(((pos[0] - min) % range) + range) % range + min, pos[1]]

CREDIT ="""
                                         _        _                                                                      
                                        | |      (_)                                                                     
  ______ ______ ______   _ __ ___   __ _| |_ __ _ _ _ __      ___  ___ _ ____   _____ _ __   ______ ______ ______ ______ 
 |______|______|______| | '_ ` _ \ / _` | __/ _` | | '__|    / __|/ _ \ '__\ \ / / _ \ '__| |______|______|______|______|
                        | | | | | | (_| | || (_| | | |       \__ \  __/ |   \ V /  __/ |                                 
                        |_| |_| |_|\__,_|\__\__,_|_|_|       |___/\___|_|    \_/ \___|_|                                 
                                                                                                                         
                                                                                                                         
  _                   _   _                                    _      _____            _    _ __  __ ______ _____        
 | |                 | \ | |                             /\   | |    |_   _|     /\   | |  | |  \/  |  ____|  __ \       
 | |__  _   _        |  \| | __ _ ___ ___  ___ _ __     /  \  | |      | |      /  \  | |__| | \  / | |__  | |  | |      
 | '_ \| | | |       | . ` |/ _` / __/ __|/ _ \ '__|   / /\ \ | |      | |     / /\ \ |  __  | |\/| |  __| | |  | |      
 | |_) | |_| |       | |\  | (_| \__ \__ \  __/ |     / ____ \| |____ _| |_   / ____ \| |  | | |  | | |____| |__| |      
 |_.__/ \__, |       |_| \_|\__,_|___/___/\___|_|    /_/    \_\______|_____| /_/    \_\_|  |_|_|  |_|______|_____/       
         __/ |                                                                                                           
        |___/                                                                                                            
                                   _                         _    _         _  _______ __  __                            
                                  | |                       | |  | |       | |/ /_   _|  \/  |                           
                                  | | ___   ___  _ __ ______| |__| | ___   | ' /  | | | \  / |                           
                              _   | |/ _ \ / _ \| '_ \______|  __  |/ _ \  |  <   | | | |\/| |                           
                             | |__| | (_) | (_) | | | |     | |  | | (_) | | . \ _| |_| |  | |                           
                              \____/ \___/ \___/|_| |_|     |_|  |_|\___/  |_|\_\_____|_|  |_|                           
                                                                                                                         
                                                                                                                         
                                                                                                                         
                                                                                                                         
  ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ 
 |______|______|______|______|______|______|______|______|______|______|______|______|______|______|______|______|______|                                                                                                                  
"""