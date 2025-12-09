import socket
import select
import asyncio
import time

class BasicSocket:
    _socket: socket.socket
    _connected: bool
    _bound: bool
    _terminated: bool
    def __init__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM | socket.SO_REUSEADDR)
        self._socket.setblocking(False)
        self._connected = False
        self._bound = False
        self._terminated = False
    
    @staticmethod
    def from_raw_socket(sock: socket.socket):
        bsock = BasicSocket()
        bsock.set_socket(sock)
        return bsock
    
    def set_socket(self, sock: socket.socket):
        if self._connected or self._bound:
            self._socket.close()
            self._connected = False
            self._bound = False
        self._terminated = False

        self._socket = sock
        self._socket.setblocking(False)
        try:
            self._socket.getsockname()
            self._bound = True
        except OSError:
            self._bound = False
        try:
            self._socket.getpeername()
            self._connected = True
        except OSError:
            self._connected = False

    def is_open(self):
        return (self._connected or self._bound) and not self._terminated
    def is_closed(self):
        return not self.is_open() and not self._terminated
    def _close(self):
        self._socket.close()
        self._terminated = True
        self._connected = False
        self._bound = False
    
    async def _recv(self, n: int, timeout: float = 10) -> bytes:
        if not self.is_open():
            raise ValueError("attempted to receive from a void socket")
        
        data = b''
        started = time.time()
        while len(data) < n:
            if time.time() - started > timeout:
                raise TimeoutError("receive timed out")
            await asyncio.sleep(0)
            readable, _, _ = select.select([self._socket], [], [])
            if len(readable) == 0:
                continue

            try:
                recv = self._socket.recv(n - len(data))
                if len(recv) == 0:
                    self._close()
                    raise ValueError("_socket.recv() returned 0 bytes (socket closed?)")
                data += recv
            except OSError:
                self._close()
                raise 
            except Exception as e:
                print(f"ignoring exception {e}: add proper handling to remove this message!")
        return data
    
    async def _send(self, data: bytes, timeout: float = 10):
        if not self.is_open():
            raise ValueError("attempted to send to a void socket")
        
        n = 0
        started = time.time()
        while n < len(data):
            if time.time() - started > timeout:
                raise TimeoutError("receive timed out")
            await asyncio.sleep(0)
            _, writeable, _ = select.select([], [self._socket], [])
            if len(writeable) == 0:
                continue

            try:
                sent = self._socket.send(data[n:])
                if sent == 0:
                    self._close()
                    raise ValueError("_socket.send() returned 0 (socket closed?)")
                n += sent
            except OSError:
                self._close()
                raise 
            except Exception as e:
                print(f"ignoring exception {e}: add proper handling to remove this message!")