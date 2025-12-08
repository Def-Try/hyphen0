import struct

from protocol.primitives._serialisable import _Serialisable

class _StructPrimitive(_Serialisable):
    def __init__(self, fmt: str):
        self.fmt = fmt
        self.size = struct.calcsize(self.fmt)

    def __repr__(self):
        return f"<StructPrimitive fmt={repr(self.fmt)}>"

    def serialise(self, data: tuple[any]) -> (int, bytes): # size, raw
        return self.size, struct.pack(self.fmt, *data)
    def deserialise(self, raw: bytes) -> (int, tuple[any]): # consumed, (decoded,)
        return self.size, (struct.unpack(self.fmt, raw[0:self.size]))

uint8  = _StructPrimitive("B")
uint16 = _StructPrimitive("H")
uint32 = _StructPrimitive("I")
int8   = _StructPrimitive("b")
int16  = _StructPrimitive("h")
int32  = _StructPrimitive("i")

class _NullTerminatedStringPrimitive(_Serialisable):
    def __repr__(self):
        return f"<NullTerminatedStringPrimitive>"

    def serialise(self, data: tuple[any]) -> (int, bytes): # size, raw
        if len(data) > 1:
            raise ValueError(f'NullTerminatedStringPrimitive expects only a single bytestring, got {len(data)} values')
        data = data[0]
        if not isinstance(data, bytes):
            raise ValueError(f'NullTerminatedStringPrimitive expects a bytestring, got {type(data).__name__}')
        if b'\0' in data:
            raise ValueError(f'NullTerminatedStringPrimitive used to encode bytestring containing NULL')
        return len(data)+1, data+b'\0'
    def deserialise(self, raw: bytes) -> (int, tuple[any]): # consumed, (decoded,)
        data = raw.split(b'\0')[0]
        return len(data)+1, (raw,)

cstring = _NullTerminatedStringPrimitive()