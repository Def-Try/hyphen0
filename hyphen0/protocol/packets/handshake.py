from protocol.packets.packet import Packet, pack

# pyright: reportInvalidTypeForm=false

class HandshakeInitiate(Packet):
    _serverbound: bool = True

    user_name: pack.cstring

class HandshakeConfirm(Packet):
    _serverbound: bool = False

    server_name: pack.cstring
    server_desc: pack.cstring
    reconnect_after: pack.uint32

class HandshakeCryptModesList(Packet):
    _serverbound: bool = True

    crypt_modes: pack.array(pack.cstring)