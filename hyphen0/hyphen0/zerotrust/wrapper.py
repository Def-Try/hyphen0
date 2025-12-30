from ..socket.protosocket import ProtoSocket
from ._layer import ZTLayer

class ZerotrustSocket(ProtoSocket):
    def __init__(self, ztlayer: ZTLayer):
        self._ztlayer = ztlayer
    @classmethod
    def cast(cls, sock: ProtoSocket, ztlayer: ZTLayer):
        assert isinstance(sock, ProtoSocket)
        sock.__class__ = cls
        sock.__init__(ztlayer)
        assert isinstance(sock, ZerotrustSocket)
        return sock
    async def _recv(self, n: int, timeout: float = 10, strict: bool = False) -> bytes:
        try:
            self._ztlayer.push_recv(await super()._recv(self._ztlayer.chunk_size, timeout, strict))
        except TimeoutError:
            if self._ztlayer.can_pull_recv():
                return self._ztlayer.pull_recv(n)
            raise
        return self._ztlayer.pull_recv(n)
    async def _send(self, data: bytes, timeout: float = 10):
        self._ztlayer.push_send(data)
        while self._ztlayer.can_pull_send():
            await super()._send(self._ztlayer.pull_send(self._ztlayer.chunk_size), timeout)