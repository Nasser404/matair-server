from time       import time

from scr.config import CLIENT_TIMEOUT
from scr.enums  import DisconnectReason


class GameClient:
    """Server-side state of one identified connection (base class of Orb, Player and Viewer)."""
    type    = None              # ClientType
    timeout = CLIENT_TIMEOUT    # seconds of silence before being dropped

    def __init__(self, client: dict, server):
        self.client         = client                # websocket_server client: {'id', 'handler', 'address'}
        self.server         = server
        self.id             = client['id']
        self.game           = None                  # Game this client is in
        self.color          = None
        self.name           = ""
        self.last_response  = time()                # last message received from this client

    def __str__(self):
        label = f"{self.type.name.lower()}#{self.id}"
        return f"{label} '{self.name}'" if self.name else label

    def send_packet(self, data: dict):
        self.server.send_packet(self.client, data)

    def kick(self, reason: DisconnectReason = DisconnectReason.NO_REASON):
        """Tell the client why, then close its connection gracefully."""
        self.server.disconnect_client(self.client, reason=reason)

    def on_identified(self):
        """Called once the client has said what it is (orb, player or viewer)."""

    def on_disconnected(self):
        """Called when the connection is gone (closed, dropped or timed out)."""
        self.leave_game()

    def on_reidentified(self):
        """Called when this connection identifies again: drop the old state before starting over."""
        self.on_disconnected()

    def leave_game(self):
        """Detach from the current game, if any."""
        if self.game is not None:
            self.game.remove_client(self)
        self.color = None
        self.game  = None
