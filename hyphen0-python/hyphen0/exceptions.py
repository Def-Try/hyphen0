class IncompleteData(Exception):
    """Raised when trying to deserialise a data value with less bytes than needed"""

class SocketFlatlined(Exception):
    """Raised when remote socket doesn't reply to initiating heartbeats properly"""

class SocketClosed(Exception):
    """Raised when client socket is closed without warning"""

class WereKicked(Exception):
    """Raised when remote server gracefully kicks the client"""
class WereDisconnected(Exception):
    """Raised when remote client gracefully disconnected from server"""