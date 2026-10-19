# Mat@ir Python Server

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

Python WebSocket server for the Mat@ir project. This server handles game logic, player connections, and real-time data synchronization between clients.

Learn more about the main Mat@ir project here: [HACKADAY PAGE](https://hackaday.io/project/202508-matir)
And the GameMaker client: [Mat@ir Game Client Repository](https://github.com/Nasser404/matair-game) 

## Features

*   Multiplayer gameplay via WebSockets.
*   Manages player connections and disconnections.
*   Relays game data between connected clients.

## Prerequisites

*   **Python:** Version 3.11+ 
*   **Pip:** Python package installer
*   **Required Libraries:**
    *   `websocket-server`

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Nasser404/matair-server.git
    cd matair-server
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The server can be configured by modifying the `config.py` file located in `scr/config.py`

| Setting | Default | Meaning |
|---|---|---|
| `SERVER_PORT` | `29920` | Port the WebSocket server listens on |
| `PING_INTERVAL` | `3` | Seconds between two pings |
| `MAX_MISSED_PINGS` | `3` | Players and viewers silent for `PING_INTERVAL × MAX_MISSED_PINGS` seconds (9 s) are disconnected |
| `ORB_TIMEOUT` | `30` | Same for the orb, longer because the ESP32 can't answer while its motors are moving pieces |
| `SEND_TIMEOUT` | `10` | A send blocked longer than this fails instead of freezing the server |
| `LOG_LEVEL` | `"INFO"` | `"DEBUG"` also logs failed sends and full tracebacks of rejected connections |

Any message from a client counts as a sign of life, not only the answers to pings.

## Usage

To start the server, run the main Python script  `main.py`

```bash
python main.py
```

The server will then start listening for WebSocket connections on the configured port. You should see output in the console indicating it's running.

> [!NOTE] 
> Ensure the game client is configured to connect to the correct IP address and port where this server is running.

### Reading the logs

Every line is timestamped and names the client, e.g. `orb#14 'ORB IVRY'`, `player#71 'AA'`, `viewer#3`.

* `Connection lost (closed without a WebSocket close frame)`: the connection ended abruptly (orb lost its Wi-Fi, browser tab closed, or the server dropped a client that timed out). The `websocket-server` library reports this as `Client must always be masked.`; the server rewords it. Harmless.
* `Connection from ... dropped by websocket_server (...)`: usually something that isn't a WebSocket client hit the port (port scanner, a browser opening the address directly...), sometimes a connection that broke in the middle of a message. That connection is closed, nothing else is affected.
* `Sending to ... failed, it will be dropped`: the client stopped receiving (dead connection). It is skipped from then on and disconnected within a few seconds.
* `... reconnected as ..., dropping the old connection`: the orb came back before its old connection timed out. The old one is closed right away.

## Project Structure 

A brief overview of the project's directory structure:

```
matair-server/
├── main.py
├── requirements.txt
├── scr/
│   ├── config.py
│   ├── enums.py
│   ├── utils.py
│   ├── chess_game/
│   │   ├── chess_board.py
│   │   └── piece/
│   │       ├── bishop.py
│   │       ├── king.py
│   │       ├── knight.py
│   │       ├── pawn.py
│   │       ├── piece_type.py
│   │       ├── queen.py
│   │       └── rook.py
│   ├── client/
│   │   ├── game_client.py
│   │   ├── orb.py
│   │   ├── player.py
│   │   └── viewer.py
│   └── server/
│       ├── game_server.py
│       └── game.py
```
