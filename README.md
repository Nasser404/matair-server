# Mat@ir Python Server

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

Python WebSocket server for the Mat@ir project. This server handles game logic, player connections, and real-time data synchronization between clients.

Learn more about the main Mat@ir project here: [HACKADAY PAGE](https://hackaday.io/project/202508-matir)
And the GameMaker client: [Mat@ir Game Client Repository](https://github.com/Nasser404/matair-game) <!-- Link to your game client repo -->

## Features

*   Multiplayer gameplay via WebSockets.
*   Manages player connections and disconnections.
*   Relays game data between connected clients.

## Prerequisites

*   **Python:** Version 3.7+ 
*   **Pip:** Python package installer
*   **Required Libraries:**
    *   `websocket-server`
    *   `numpy`

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

## Usage

To start the server, run the main Python script  `main.py`

```bash
python main.py
```

The server will then start listening for WebSocket connections on the configured port. You should see output in the console indicating it's running.

> [!NOTE] 
> Ensure the game client is configured to connect to the correct IP address and port where this server is running.

## Project Structure 

A brief overview of the project's directory structure:

```
matair-server/
├── main.py
├── requirements.txt
├── config.py
├── enums.py
├── utils.py
├── scr/
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
│       ├── game.py
```
