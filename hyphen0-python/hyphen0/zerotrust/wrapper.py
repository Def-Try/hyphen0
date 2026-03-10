import socket
import time

from ..socket.protosocket import ProtoSocket
from ._layer import ZTLayer

class ZerotrustSocket(ProtoSocket):
    def __init__(self, *args, noinit: bool = False, ztlayer: ZTLayer = None, **kwargs):
        if not noinit: super().__init__(*args, **kwargs)
        self._ztlayer = ztlayer
    @classmethod
    def cast(cls, sock: ProtoSocket, ztlayer: ZTLayer):
        assert isinstance(sock, ProtoSocket)
        sock.__class__ = cls
        sock.__init__(noinit=True, ztlayer=ztlayer)
        assert isinstance(sock, ZerotrustSocket)
        return sock
    
    def from_raw_socket(self, sock: socket.socket):
        bsock = super().from_raw_socket(sock)
        bsock._ztlayer = self._ztlayer
        return bsock

    async def _recv(self, n: int, timeout: float = 10, strict: bool = False) -> bytes:
        # print(f"[ZEROTRUST] recv {n} bytes, timeout {timeout} strict {strict}")
        data = b''
        started = time.time()
        while (strict and len(data) < n) or len(data) == 0:
            try:
                self._ztlayer.push_recv(await super()._recv(self._ztlayer.chunk_size, timeout - (time.time() - started), False))
            except TimeoutError:
                if not strict and self._ztlayer.can_pull_recv():
                    return self._ztlayer.pull_recv(n - len(data))
                raise
            data += self._ztlayer.pull_recv(n - len(data))
        return data
    async def _send(self, data: bytes, timeout: float = 10):
        # print(f"[ZEROTRUST] send {data} timeout {timeout}")
        self._ztlayer.push_send(data)
        while self._ztlayer.can_pull_send():
            await super()._send(self._ztlayer.pull_send(self._ztlayer.chunk_size), timeout)