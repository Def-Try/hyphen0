from .basicsocket import BasicSocket
from ..packets.packet import Packet, pack, HeartbeatClientbound, HeartbeatServerbound

from collections import deque
from typing import Deque, Type, List

from ..exceptions import IncompleteData, SocketFlatlined

import time
import asyncio
import random

class ProtoSocket(BasicSocket):
    def __init__(self, serverbound: bool = False,
                        heartbeat_interval: int = 10, max_heartbeat_misses: int = 5,
                *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serverbound = serverbound
        self._inbound: Deque[Packet] = deque()
        self._outbound: Deque[Packet] = deque()
        self._recv_buffer: bytes = b''
        self._last_packet_received: int = time.time() - (heartbeat_interval / 2) if serverbound else time.time()
        self._heartbeat_interval: int = heartbeat_interval # if serverbound else heartbeat_interval * 1.5
        self._missed_heartbeats: int = 0
        self._max_heartbeat_misses: int = max_heartbeat_misses
        self._heartbeat_nonce: int = None
        self._heartbeat_incoming = HeartbeatClientbound if serverbound else HeartbeatServerbound
        self._heartbeat_outgoing = HeartbeatServerbound if serverbound else HeartbeatClientbound

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
        if isinstance(read, self._heartbeat_incoming):
            if read.initiating:
                # print(f"received initiating heartbeat, nonce={read.nonce}")
                self._missed_heartbeats = 0
                self._heartbeat_nonce = None
                # print(f"sending reply heartbeat, nonce={read.nonce}")
                await self._write_packet(self._heartbeat_outgoing(nonce=read.nonce, initiating=False))
                self._last_packet_received = time.time() + 1
            else:
                if read.nonce != self._heartbeat_nonce:
                    pass
                    # print("bad nonce on heartbeat packet. are we running behind or ahead?")
                else:
                    # print(f"received reply heartbeat, nonce={read.nonce}")
                    self._missed_heartbeats = 0
                    self._heartbeat_nonce = None
                self._last_packet_received = time.time()
            read = None

        if read is not None:
            self._inbound.append(read)
            self._last_packet_received = time.time()
        elif time.time() - self._last_packet_received > self._heartbeat_interval:
            if self._heartbeat_nonce:
                # print(f"missed heartbeat! count={self._missed_heartbeats}")
                self._missed_heartbeats += 1
            if self._missed_heartbeats > self._max_heartbeat_misses:
                raise SocketFlatlined(f"missed {self._missed_heartbeats} heartbeats")
            self._last_packet_received = time.time()
            self._heartbeat_nonce = random.randint(0, 2**32-1)
            # print(f"sending initiating heartbeat, nonce={self._heartbeat_nonce}")
            await self._write_packet(self._heartbeat_outgoing(nonce=self._heartbeat_nonce, initiating=True))
        
        if self.outbound_pending() > 0:
            await self._write_packet(self._outbound.popleft(), timeout)

    def inbound_pending(self):
        return len(self._inbound) > 0
    def outbound_pending(self):
        return len(self._outbound) > 0

    def read_packet(self) -> Packet:
        return None if not self.inbound_pending() else self._inbound.popleft()
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