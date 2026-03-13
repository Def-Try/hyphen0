from .packet import Packet, pack

# pyright: reportInvalidTypeForm=false

class HandshakeInitiate(Packet):
    """Sent by client to server immediately after connection.
    Doesn't serve any purpose other than to verify that client is of ours protocol."""
    _serverbound: bool = True

class HandshakeConfirm(Packet):
    """Sent by server to client in response to HandshakeInitiate.
    Doesn't serve any purpose other than to verify that server is of ours protocol."""
    _serverbound: bool = False

class HandshakeCancel(Packet):
    """Sent by server to client in case if handshake failed at any point during it, immediately closing the connection after.
    Contains a human-readable message, probably describing what went wrong."""
    _serverbound: bool = False

    message: pack.cstring

class HandshakeOK(Packet):
    """Sent by client to server after handshake has been finalised, before passing the control over to user code.
    If that packet isn't sent, server kills the connection on timeout automatically."""
    _serverbound: bool = True

class HandshakeCryptModesList(Packet):
    """Sent by client to server during handshake and before encryption has been set up to list modes it supports."""
    _serverbound: bool = True

    crypt_modes: pack.array(pack.cstring)

class HandshakeCryptModeSelect(Packet):
    """Sent by server to client during handshake and before encryption has been set up to select mode for this session."""
    _serverbound: bool = False

    crypt_mode: pack.cstring

class HandshakeCryptKEXServer(Packet):
    """Sent by server to client during handshake and before encryption has been set up to exchange public key and session key parameters."""
    _serverbound: bool = False
    salt: pack.fixed(32)
    key_len: pack.uint16
    public_key: pack.cstring

class HandshakeCryptKEXClient(Packet):
    """Sent by client to server during handshake and before encryption has been set up to exchange public key."""
    _serverbound: bool = True
    public_key: pack.cstring

class HandshakeCryptOK(Packet):
    """Sent by server to client during handshake right before enabling encryption to notify the client to do the same."""
    _serverbound: bool = False

class HandshakeCryptTestPing(Packet):
    """Sent by client to server during handshake and after encryption has been enabled to test connectivity"""
    _serverbound: bool = True

    test: pack.fixed(512)
class HandshakeCryptTestPong(Packet):
    """Sent by server to client during handshake and after encryption has been enabled to test connectivity."""
    _serverbound: bool = False

    test: pack.fixed(512)