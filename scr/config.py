SERVER_HOST         = "0.0.0.0"
SERVER_PORT         = 29920
SERVER_VERSION      = "1.3"     # sent to every client on connect

PING_INTERVAL       = 3         # seconds between two pings
MAX_MISSED_PINGS    = 3
CLIENT_TIMEOUT      = PING_INTERVAL * MAX_MISSED_PINGS  # players/viewers (and unidentified connections) silent this long are dropped
ORB_TIMEOUT         = 30        # orbs get longer: the ESP32 can't answer while its motors move the pieces

SEND_TIMEOUT        = 2         # seconds a send may block; a client whose send fails is then skipped and dropped
LOG_LEVEL           = "INFO"
