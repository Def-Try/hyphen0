from .basicsocket import BasicSocket
from ..packets.packet import Packet

from collections import deque
from typing import Deque, Type, List

from ..exceptions import IncompleteData

import time
import asyncio

class ProtoSocket(BasicSocket):
    def __init__(self, serverbound: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serverbound = serverbound
        self._inbound: Deque[Packet] = deque()
        self._outbound: Deque[Packet] = deque()
        self._recv_buffer: bytes = b''

    async def _read_packet(self, timeout: float = 10) -> Packet:
        try:
            self._recv_buffer += await self._recv(1024, timeout)
        except TimeoutError:
            pass
        try:
            consumed, packet = Packet.deserialise(self._recv_buffer, not self._serverbound)
            self._recv_buffer = self._recv_buffer[consumed:]
            return packet
        except IncompleteData:
            pass
    async def _write_packet(self, packet: Packet, timeout: float = 10):
        serialised = packet.serialise(self._serverbound)
        await self._send(serialised, timeout)

    async def update(self, timeout: float = 10):
        read = await self._read_packet(timeout)
        if read is not None:
            self._inbound.append(read)
        
        if len(self._outbound) > 0:
            await self._write_packet(self._outbound.popleft(), timeout)

    def read_packet(self) -> Packet:
        return self._inbound.popleft()
    def write_packet(self, packet: Packet):
        self._outbound.append(packet)
    async def wait_for_packet(self, ptype: Type[Packet]|List[Type[Packet]], timeout: float = 10) -> Packet:
        started = time.time()
        while True:
            await asyncio.sleep(0)
            if time.time() - started > timeout:
                raise TimeoutError("packet did not appear before timeout expiry")
            for i in self._inbound:
                if isinstance(ptype, list):
                    for j in ptype:
                        if not isinstance(i, j): continue
                        self._inbound.remove(i)
                        return i
                    continue
                if not isinstance(i, ptype): continue
                self._inbound.remove(i)
                return i