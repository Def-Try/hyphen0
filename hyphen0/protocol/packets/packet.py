import sys
if sys.version_info.major == 3 and sys.version_info.minor >= 14:
    from annotationlib import Format as annotationlib_Format # type: ignore[import-not-found]

import protocol.primitives.basic as pack
from protocol.primitives._serialisable import _Serialisable
from protocol.exceptions import IncompleteData

# pyright: reportInvalidTypeForm=false

REGISTERED_PACKETS = {
    "clientbound": {},
    "serverbound": {},
}

pid_prim = pack.uint8

class PacketMeta(type):
    _next_serverbound_pid: int = 0
    _next_clientbound_pid: int = 0
    def __new__(cls, clsname, bases, namespace):
        serverbound = namespace.get("_serverbound", None)
        if serverbound == None:
            return super().__new__(cls, clsname, bases, namespace)
        if not isinstance(serverbound, bool):
            raise ValueError("_serverbound of Packet should be a boolean")
        hints = namespace.get("__annotations__", {})
        if annotationlib_Format: # i have no clue why python 3.14 changed that, but now we have to generate annotations and i HATE it
            hints = namespace['__annotate_func__'](annotationlib_Format.VALUE)

        namespace['_fields'] = [('_pid', pid_prim)]

        for fname, ftype in hints.items():
            if fname.startswith("_"):
                continue
            if ftype == _Serialisable:
                raise ValueError("field in Packet is a raw _Serialisable")
            if not isinstance(ftype, _Serialisable) and not issubclass(ftype, pack.cstruct):
                raise ValueError("field in Packet is not a _Serialisable")
            namespace['_fields'].append((fname, ftype))
        namespace['_pid'] = cls._next_serverbound_pid if serverbound else cls._next_clientbound_pid
        cls._next_serverbound_pid += 1 if serverbound else 0
        cls._next_clientbound_pid += 0 if serverbound else 1

        # print(f"registering {namespace['__qualname__']} as pid {namespace['_pid']}")

        this = super().__new__(cls, clsname, bases, namespace)

        REGISTERED_PACKETS['serverbound' if serverbound else 'clientbound'][namespace['_pid']] = this

        return this

class Packet(_Serialisable, metaclass=PacketMeta):
    _pid: int
    _serverbound: bool
    _fields: tuple[str, _Serialisable]

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        reprd = f"{self.__class__.__name__}("
        for k,v in self.__dict__.items():
            reprd += f"{k}={repr(v)}, "
        if self.__dict__ != {}: reprd = reprd[:-2]
        reprd += ")"
        return reprd

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
            _, ser = ftype.serialise((getattr(self, fname),))
            raw += ser
        return raw
    @staticmethod
    def deserialise(raw, serverbound: bool) -> tuple[int, Packet]: # consumed, deserialised packet
        cns = 0
        _, (pid,) = pid_prim.deserialise(raw)
        packet_cls = Packet.find_by_pid(pid, serverbound)
        fields = {}
        for fname, ftype in packet_cls._fields:
            if raw == b'':
                raise IncompleteData()
            consumed, (decoded,) = ftype.deserialise(raw)
            cns += consumed
            raw = raw[consumed:]
            fields[fname] = decoded
        return cns, packet_cls(**fields)

class HeartbeatClientbound(Packet):
    _serverbound: bool = False
    initiating: pack.boolean
    nonce: pack.uint32
class HeartbeatServerbound(Packet):
    _serverbound: bool = True
    initiating: pack.boolean
    nonce: pack.uint32
class Kick(Packet):
    _serverbound: bool = False
    message: pack.cstring
class Disconnect(Packet):
    _serverbound: bool = True
    message: pack.cstring
