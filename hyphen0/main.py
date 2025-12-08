import protocol.packets.packet as packet

exit()


# --------------------------------------------------------------
# demo.py – shows how the pieces fit together
# --------------------------------------------------------------
from typing import Tuple

# --------------------------------------------------------------
# exceptions that the public API raises
# --------------------------------------------------------------
class PacketError(RuntimeError):
    """Base class for all packet‑related errors."""

class UnregisteredPacket(PacketError):
    """Raised when an unknown packet id appears on the wire."""
    def __init__(self, pid: int):
        super().__init__(f"Packet id {pid:#02x} is not registered")
        self.pid = pid

class AlreadyRegistered(PacketError):
    """Raised when a packet class tries to claim an id that is taken."""
    def __init__(self, pid: int, cls):
        super().__init__(f"Packet id {pid:#02x} already used by {cls.__name__}")
        self.pid = pid
        self.cls = cls

# --------------------------------------------------------------
# Global lookup tables – two namespaces are kept separate
# --------------------------------------------------------------
REGISTERED_PACKETS = {
    "clientbound": {},   # pid → class
    "serverbound": {},   # pid → class
}


# --------------------------------------------------------------
# Metaclass – runs once per subclass definition
# --------------------------------------------------------------
class PacketMeta(type):
    """Collects field information, builds a struct format string,
    assigns a free pid, and registers the class."""

    _next_pid = {False: 0, True: 0}         # per‑direction allocators

    def __new__(mcls, name, bases, namespace, **kw):
        # -----------------------------------------------------------------
        # 1️⃣  Decide direction (client → server or vice‑versa)
        # -----------------------------------------------------------------
        serverbound = bool(namespace.get("_serverbound", False))

        # -----------------------------------------------------------------
        # 2️⃣  Pull out the annotated fields that are primitives
        # -----------------------------------------------------------------
        hints = namespace.get("__annotations__", {})
        field_names = []
        fmt_parts = []

        for fname, ftype in hints.items():
            # ignore private attributes that start with '_' – they are not on‑wire
            if fname.startswith("_"):
                continue

            # we only support the primitive descriptors defined in utils
            if isinstance(ftype, _Primitive):
                fmt_parts.append(ftype.fmt)
                field_names.append(fname)
            else:                     # user supplied a default value of a primitive
                default = namespace.get(fname, None)
                if isinstance(default, _Primitive):
                    fmt_parts.append(default.fmt)
                    field_names.append(fname)
                else:
                    raise TypeError(
                        f"Field '{fname}' of packet '{name}' must be a primitive "
                        f"descriptor (uint8, uint16, …) or a default value of one."
                    )

        # -----------------------------------------------------------------
        # 3️⃣  Build a struct object (little‑endian) that knows how to pack/unpack
        # -----------------------------------------------------------------
        struct_fmt = "<" + "".join(fmt_parts)   # little‑endian, packed without padding
        payload_struct = struct.Struct(struct_fmt)

        # -----------------------------------------------------------------
        # 4️⃣  Pick a free pid for this direction
        # -----------------------------------------------------------------
        pid = mcls._next_pid[serverbound]
        if pid > 0xFF:
            raise RuntimeError("Out of packet ids for this direction")
        mcls._next_pid[serverbound] = pid + 1

        # -----------------------------------------------------------------
        # 5️⃣  Create the class object
        # -----------------------------------------------------------------
        cls = super().__new__(mcls, name, bases, dict(namespace))
        cls._serverbound = serverbound
        cls._pid = pid
        cls._field_names = tuple(field_names)
        cls._struct = payload_struct

        # -----------------------------------------------------------------
        # 6️⃣  Register the class in the global tables
        # -----------------------------------------------------------------
        direction = "serverbound" if serverbound else "clientbound"
        if pid in REGISTERED_PACKETS[direction]:
            raise AlreadyRegistered(pid, cls)
        REGISTERED_PACKETS[direction][pid] = cls

        return cls


# --------------------------------------------------------------
# utils – primitive descriptors (uint8, uint16, …)
# --------------------------------------------------------------
import struct
from typing import NewType

class _Primitive:
    __slots__ = ("fmt", "size")
    def __init__(self, fmt: str):
        self.fmt = fmt
        self.size = struct.calcsize(fmt)

    def __repr__(self):
        return f"<Primitive fmt={self.fmt}>"

# expose a handful of common primitives; the names are deliberately
# identical to the ones you used in the question.
uint8  = _Primitive("B")   # unsigned 8‑bit
uint16 = _Primitive("H")   # unsigned 16‑bit, little‑endian
uint32 = _Primitive("I")   # unsigned 32‑bit, little‑endian
int8   = _Primitive("b")
int16  = _Primitive("h")
int32  = _Primitive("i")

# --------------------------------------------------------------
# PUBLIC API – what a user of the library sees
# --------------------------------------------------------------

class Packet(metaclass=PacketMeta):
    """Base class for every packet.

    Sub‑class it, declare a `serverbound` flag and annotate the fields
    you want to transmit.  Nothing else is needed – the metaclass will
    do the rest.
    """
    # the two attributes that the metaclass looks at
    _serverbound: bool = False          # client‑-> server if True
    _pid: int = -1                      # filled in by the metaclass

    # -----------------------------------------------------------------
    # Helper methods that *users* may want to call
    # -----------------------------------------------------------------
    def serialise(self) -> bytes:
        """Return the binary representation of the packet:  
        ``<pid><payload>`` where ``pid`` is a single unsigned byte."""
        payload = self._struct.pack(*(getattr(self, f) for f in self._field_names))
        return bytes([self._pid]) + payload

    @classmethod
    def deserialise(cls, raw: bytes) -> "Packet":
        """Create the appropriate subclass from ``raw``.  

        ``raw`` must contain at least one byte (the packet id).  The rest
        of the buffer is interpreted according to the layout that was
        discovered by the metaclass.
        """
        if not raw:
            raise PacketError("Empty buffer")
        pid = raw[0]
        try:
            pkt_cls = REGISTERED_PACKETS['clientbound' if not cls._serverbound else 'serverbound'][pid]
        except KeyError:
            raise UnregisteredPacket(pid) from None
        payload = raw[1:]
        if len(payload) != pkt_cls._struct.size:
            raise PacketError(f"Payload size mismatch for {pkt_cls.__name__}")
        values = pkt_cls._struct.unpack(payload)
        obj = pkt_cls.__new__(pkt_cls)          # bypass __init__
        for name, value in zip(pkt_cls._field_names, values):
            setattr(obj, name, value)
        return obj

# == import the infrastructure (the code above) ==
# from packet_lib import Packet, REGISTERED_PACKETS, \
#     uint8, uint16, uint32, PacketError, UnregisteredPacket

# -- define packets ------------------------------------------------
class Handshake(Packet):
    _serverbound = True
    session_id: uint32
    protocol_version: uint8 = uint8   # default value, still a primitive

class ChatMessage(Packet):
    # client → server (default serverbound=False)
    sender_id: uint16
    message_len: uint8                # we will send the length explicitly
    # Note: you could also implement a `bytes` field with a custom
    # packer/unpacker if you need variable‑length payloads.

class ServerTick(Packet):
    tick: uint32

# --------------------------------------------------------------
# Serialize a packet
# --------------------------------------------------------------
msg = Handshake()
msg.session_id = 0xAABBCCDD
msg.protocol_version = 1
wire = msg.serialise()          # b'\x00' + struct.pack("<IB", 0xAABBCCDD, 1)

# --------------------------------------------------------------
# Decode it on the other side
# --------------------------------------------------------------
received = Packet.deserialise(wire)          # returns a Handshake instance
assert isinstance(received, Handshake)
assert received.session_id == 0xAABBCCDD
assert received.protocol_version == 1

# --------------------------------------------------------------
# Show the registration tables
# --------------------------------------------------------------
print("Client‑bound packets:", REGISTERED_PACKETS["clientbound"])
print("Server‑bound packets:", REGISTERED_PACKETS["serverbound"])
# Output (ids may differ):
#   Server‑bound packets: {0: <class '__main__.Handshake'>}
#   Client‑bound packets: {0: <class '__main__.ChatMessage'>, 1: <class '__main__.ServerTick'>}
