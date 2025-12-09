from .packet import Packet, pack

# pyright: reportInvalidTypeForm=false

class ChatSendMessage(Packet):
    _serverbound: bool = True

    content: pack.cstring

class ChatMessage(Packet):
    _serverbound: bool = False

    user_name: pack.cstring
    content: pack.cstring