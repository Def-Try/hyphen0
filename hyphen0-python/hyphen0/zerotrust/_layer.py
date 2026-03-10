class ZTLayer:
    chunk_size: int = 1024
    recv_buffer: bytes = b''
    send_buffer: bytes = b''
    unwrapped_recv_buffer: bytes = b''

    def wrap(data: bytes) -> bytes:
        raise NotImplementedError
    def unwrap(data: bytes) -> tuple[int, bytes]:
        raise NotImplementedError
    
    def can_pull_send(self) -> bool:
        return len(self.send_buffer) > 0
    def can_pull_recv(self) -> bool:
        return len(self.unwrapped_recv_buffer + self.recv_buffer) > 0
    def push_recv(self, data: bytes):
        self.recv_buffer += data
    def push_send(self, data: bytes):
        self.send_buffer += data
    def pull_recv(self, n: int) -> bytes:
        if not self.can_pull_recv():
            return b""
        if len(self.recv_buffer) > 0:
            pulled, recvd = self.unwrap(self.recv_buffer)
        else:
            pulled, recvd = 0, b''
        recvd = self.unwrapped_recv_buffer + recvd
        self.recv_buffer = self.recv_buffer[pulled:]
        if len(recvd) > n:
            self.unwrapped_recv_buffer = recvd[n:]
            recvd = recvd[:n]
        return recvd
    def pull_send(self, n: int) -> bytes:
        if not self.can_pull_send():
            return b""
        tsend = self.send_buffer[:n]
        self.send_buffer = self.send_buffer[n:]
        return self.wrap(tsend)