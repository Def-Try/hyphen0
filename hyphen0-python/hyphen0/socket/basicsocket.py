import socket
import select
import asyncio
import time

from ..exceptions import SocketClosed

class BasicSocket:
    _socket: socket.socket
    _connected: bool
    _bound: bool
    _terminated: bool
    def __init__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(False)
        self._connected = False
        self._bound = False
        self._terminated = False
        self._nicename = None
    
    @classmethod
    def from_raw_socket(cls, sock: socket.socket):
        bsock = cls()
        bsock.set_socket(sock)
        return bsock

    def getnicename(self) -> str:
        if self._nicename: return self._nicename
        host, port = self._socket.getpeername()
        self._nicename = f"{host}:{port}"
        return self._nicename
    
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

    def connect(self, host: str, port: int):
        try:
            self._socket.setblocking(True)
            self._socket.settimeout(10)
            self._socket.connect((host, port))
            self._socket.setblocking(False)
            self._connected = True
        except Exception:
            raise

    def bind(self, interface: str, port: int, max_clients: int = 8):
        try:
            self._socket.setblocking(True)
            self._socket.bind((interface, port))
            self._socket.listen(max_clients)
            self._socket.setblocking(False)
            self._bound = True
        except Exception:
            raise

    def is_open(self):
        return (self._connected or self._bound) and not self._terminated
    def is_closed(self):
        return not self.is_open() and not self._terminated
    def _close(self):
        self._socket.close()
        self._terminated = True
        self._connected = False
        self._bound = False
    def close(self):
        return self._close()

    async def accept(self):
        if not self.is_open():
            raise ValueError("attempted to receive from a void socket")
        if not self._bound:
            raise ValueError("attempted to accept from a connected socket")
        while True:
            await asyncio.sleep(0)
            try:
                readable, _, _ = select.select([self._socket], [], [], 0)
            except ValueError:
                raise SocketClosed()
            if len(readable) == 0:
                continue
            nsock, addr = self._socket.accept()
            sock = self.from_raw_socket(nsock)
            sock._bound = False
            sock._connected = True
            return sock, addr
    
    async def _recv(self, n: int, timeout: float = 10, strict: bool = False) -> bytes:
        if not self.is_open():
            raise ValueError("attempted to receive from a void socket")
        if self._bound:
            raise ValueError("attempted to receive from a bound socket")
        
        data = b''
        started = time.time()
        while (strict and len(data) < n) or len(data) == 0:
            await asyncio.sleep(0)
            try:
                readable, _, _ = select.select([self._socket], [], [], 0)
            except ValueError:
                raise SocketClosed()
            if len(readable) == 0:
                if time.time() - started > timeout:
                    raise TimeoutError("receive timed out")
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
        if self._bound:
            raise ValueError("attempted to send to a bound socket")
        
        n = 0
        started = time.time()
        while n < len(data):
            await asyncio.sleep(0)
            try:
                _, writeable, _ = select.select([], [self._socket], [], 0)
            except ValueError:
                raise SocketClosed()
            if len(writeable) == 0:
                if time.time() - started > timeout:
                    raise TimeoutError("write timed out")
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