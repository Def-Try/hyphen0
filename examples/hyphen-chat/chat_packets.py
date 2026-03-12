"""
Custom packets for chat application using hyphen0 protocol.
"""
import hyphen0.primitives.basic as pack
from hyphen0.packets.packet import Packet

class ChatRegisterServerbound(Packet):
    """Client sends info about itself to server"""
    _serverbound: bool = True
    username: pack.cstring

class ChatRegisterClientbound(Packet):
    """Server confirms client info about it"""
    _serverbound: bool = False
    username: pack.cstring

class ChatMessageServerbound(Packet):
    """Client sends chat message to server"""
    _serverbound: bool = True
    message: pack.cstring

class ChatMessageClientbound(Packet):
    """Server broadcasts chat message to all clients"""
    _serverbound: bool = False
    message: pack.cstring
    sender: pack.cstring
    timestamp: pack.uint64

class UserJoinClientbound(Packet):
    """Server notifies clients about new user"""
    _serverbound: bool = False
    username: pack.cstring

class UserLeaveClientbound(Packet):
    """Server notifies clients about user leaving"""
    _serverbound: bool = False
    username: pack.cstring

class UserListClientbound(Packet):
    """Server sends list of connected users to client"""
    _serverbound: bool = False
    users: pack.array(pack.cstring)