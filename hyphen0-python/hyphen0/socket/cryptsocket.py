from .protosocket import ProtoSocket

from ..encryption._crypter import _Crypter
from ..packets.packet import Packet, pack
from ..exceptions import IncompleteData

class CryptSocket(ProtoSocket):
    _encryption = None

    def __init__(self, _socket):
        self._encryption = None

    def __new__(cls, sock: ProtoSocket):
        assert isinstance(sock, ProtoSocket)
        sock.__class__ = cls
        assert isinstance(sock, cls)
        return sock
    
    def set_encryption(self, crypter: _Crypter|None):
        if crypter == None:
            self._encryption = None
            return
        if not isinstance(crypter, _Crypter):
            raise ValueError("crypter has to be instance of _Crypter or None")
        self._encryption = crypter
    
    async def _read_packet(self, timeout: float = 10) -> Packet:
        if self._encryption == None:
            raise ValueError("CryptSocket should have encryption set before reading packets")
            # return await super()._read_packet(timeout)
        try:
            _, (size,) = pack.uint32.deserialise(await self._recv(4, timeout, True))
            crypted = await self._recv(size, timeout, True)
            decrypted = self._encryption.decrypt(crypted)
            _, packet = Packet.deserialise(decrypted, not self._serverbound)
            return packet
        except TimeoutError:
            pass
    async def _write_packet(self, packet: Packet, timeout: float = 10):
        if self._encryption == None:
            raise ValueError("CryptSocket should have encryption set before write packets")
            # return await super()._write_packet(packet, timeout)
        try:
            serialised = packet.serialise(self._serverbound)
            crypted = self._encryption.encrypt(serialised)
            _, size = pack.uint32.serialise((len(crypted),))
            await self._send(size+crypted, timeout)
        except TimeoutError:
            pass