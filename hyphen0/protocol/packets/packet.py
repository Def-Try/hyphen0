import struct

import protocol.primitives.basic as pack
from protocol.primitives._serialisable import _Serialisable

REGISTERED_PACKETS = {
    "clientbound": {},
    "serverbound": {},
}

pid_prim = pack.uint8

class PacketMeta(type):
    _next_serverbound_pid: int = 0
    _next_clientbound_pid: int = 0
    def __new__(cls, clsname, bases, namespace):
        serverbound = bool(namespace.get("_serverbound", False))
        if not isinstance(serverbound, bool):
            raise ValueError("_serverbound of Packet should be a boolean")
        hints = namespace.get("__annotations__", {})

        namespace['_fields'] = [('_pid', pid_prim)]

        for fname, ftype in hints.items():
            if fname.startswith("_"):
                continue
            if ftype == _Serialisable:
                raise ValueError("field in Packet is a raw _Serialisable")
            if not isinstance(ftype, _Serialisable):
                raise ValueError("field in Packet is not a _Serialisable")
            namespace['_fields'].append((fname, ftype))
        namespace['_pid'] = _next_serverbound_pid if serverbound else _next_clientbound_pid
        _next_serverbound_pid += 1 if serverbound else 0
        _next_clientbound_pid += 0 if serverbound else 1

        return super().__new__(cls, clsname, bases, namespace)

class Packet(metaclass=PacketMeta):
    _pid: int
    _serverbound: bool
    _fields: tuple[str, _Serialisable]

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    @staticmethod
    def find_by_pid(pid: int, serverbound: bool):
        if not isinstance(serverbound, bool):
            raise ValueError("serverbound should be a boolean")
        packet = REGISTERED_PACKETS['serverbound' if serverbound else 'clientbound'].get(pid, None)
        if not packet:
            raise ValueError(f"packet in {'serverbound' if serverbound else 'clientbound'} realm with PID={pid} not found")
        return packet

    def serialise(self, serverbound: bool) -> bytes:
        if self._serverbound != serverbound:
            raise ValueError("attempting to serialise non-serverbound packet for serverbound sending")
        raw = b''
        for fname, ftype in self._fields:
            _, ser = ftype.serialise(getattr(self, fname))
            raw += ser
        return raw
    @staticmethod
    def deserialise(raw, serverbound: bool):
        _, pid = pid.deserialise(raw)
        packet_cls = self.find_by_pid(pid, serverbound)
        fields = {}
        for fname, ftype in packet_cls._fields:
            consumed, decoded = ftype.deserialise(raw)
            raw = raw[consumed:]
            fields[fname] = decoded
        return packet_cls(*fields)

class TestPacket(Packet):
    test: pack.uint8 = 0
    cstr: pack.cstring = 'hello world'

print(TestPacket().serialise())