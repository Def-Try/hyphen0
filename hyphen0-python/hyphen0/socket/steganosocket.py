import time
import socket

from .basicsocket import BasicSocket
from ..stegano._layer import SteganoLayer

class SteganoSocket(BasicSocket):
    _steganolayer: SteganoLayer|None = None
    def __init__(self, steganolayer: SteganoLayer|None = None):
        super().__init__()
        self._steganolayer = steganolayer
        
    async def _recv(self, n: int, timeout: float = 10, strict: bool = False) -> bytes:
        if not self._steganolayer: return await super()._recv(n, timeout, strict)

        data = b''
        started = time.time()
        while (strict and len(data) < n) or len(data) == 0:
            try:
                self._steganolayer.push_recv(await super()._recv(self._steganolayer.chunk_size, timeout - (time.time() - started), False))
            except TimeoutError:
                if self._steganolayer.can_pull_recv():
                    data += self._steganolayer.pull_recv(n - len(data))
                if not strict:
                    return data
                if len(data) == n:
                    return data
                raise
            data += self._steganolayer.pull_recv(n - len(data))
        return data
        
    async def _send(self, data: bytes, timeout: float = 10):
        if not self._steganolayer: return await super()._send(data, timeout)

        self._steganolayer.push_send(data)
        while self._steganolayer.can_pull_send():
            await super()._send(self._steganolayer.pull_send(self._steganolayer.chunk_size), timeout)
    
    async def _accept(self):
        sock, addr = await super()._accept()
        if self._steganolayer:
            sock._steganolayer = type(self._steganolayer)()
            sock._steganolayer.set_serverbound(self._steganolayer.serverbound)
        return sock, addr
        