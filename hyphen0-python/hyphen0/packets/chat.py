from .packet import Packet, pack

# pyright: reportInvalidTypeForm=false

class ChatUserInfo(pack.cstruct):
    username: pack.cstring

class ChatUserAuthenticate(Packet):
    _serverbound: bool = True

    uinfo: ChatUserInfo

class ChatUserAdd(Packet):
    _serverbound: bool = False

    uid: pack.uint8
    uinfo: ChatUserInfo
class ChatUserRemove(Packet):
    _serverbound: bool = False

    uid: pack.uint8

class ChatSendMessage(Packet):
    _serverbound: bool = True

    nonce: pack.uint32
    content: pack.cstring

class ChatMessage(Packet):
    _serverbound: bool = False

    nonce: pack.uint32
    uid: pack.uint8
    content: pack.cstring
class ChatSVMessage(Packet):
    _serverbound: bool = False

    sender: pack.cstring
    content: pack.cstring