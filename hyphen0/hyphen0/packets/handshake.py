from .packet import Packet, pack

# pyright: reportInvalidTypeForm=false

class HandshakeInitiate(Packet):
    _serverbound: bool = True
class HandshakeConfirm(Packet):
    _serverbound: bool = False
class HandshakeCancel(Packet):
    _serverbound: bool = False

    message: pack.cstring
class HandshakeOK(Packet):
    _serverbound: bool = True

class HandshakeCryptModesList(Packet):
    _serverbound: bool = True

    crypt_modes: pack.array(pack.cstring)
class HandshakeCryptModeSelect(Packet):
    _serverbound: bool = False

    crypt_mode: pack.cstring
class HandshakeCryptOK(Packet):
    _serverbound: bool = False

class HandshakeCryptKEXClient(Packet):
    _serverbound: bool = True
    public_key: pack.cstring
class HandshakeCryptKEXServer(Packet):
    _serverbound: bool = False
    salt: pack.fixed(32)
    key_len: pack.uint16
    public_key: pack.cstring

class HandshakeCryptTestPing(Packet):
    _serverbound: bool = True

    test: pack.fixed(512)
class HandshakeCryptTestPong(Packet):
    _serverbound: bool = False

    test: pack.fixed(512)