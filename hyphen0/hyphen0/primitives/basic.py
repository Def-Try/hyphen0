import struct

annotationlib_Format = None
import sys
if sys.version_info.major == 3 and sys.version_info.minor >= 14:
    from annotationlib import Format as annotationlib_Format # type: ignore[import-not-found]
else:
    annotationlib_Format = None

from hyphen0.primitives._serialisable import _Serialisable
from hyphen0.exceptions import IncompleteData

class _StructPrimitive(_Serialisable):
    def __init__(self, fmt: str):
        self.fmt = fmt
        self.size = struct.calcsize(self.fmt)

    def __repr__(self):
        return f"<StructPrimitive fmt={repr(self.fmt)}>"

    def serialise(self, data: tuple[any]) -> tuple[int, bytes]: # size, raw
        return self.size, struct.pack(self.fmt, *data)
    def deserialise(self, raw: bytes) -> tuple[int, tuple[any]]: # consumed, (decoded,)
        if len(raw) < self.size:
            raise IncompleteData()
        return self.size, (struct.unpack(self.fmt, raw[0:self.size]))

uint8   = _StructPrimitive("B")
uint16  = _StructPrimitive("H")
uint32  = _StructPrimitive("I")
int8    = _StructPrimitive("b")
int16   = _StructPrimitive("h")
int32   = _StructPrimitive("i")
boolean = _StructPrimitive("?")

class _NullTerminatedStringPrimitive(_Serialisable):
    def __repr__(self):
        return f"<NullTerminatedStringPrimitive>"

    def serialise(self, data: tuple[any]) -> tuple[int, bytes]: # size, raw
        if len(data) > 1:
            raise ValueError(f'NullTerminatedStringPrimitive expects only a single bytestring, got {len(data)} values')
        data = data[0]
        if not isinstance(data, bytes):
            raise ValueError(f'NullTerminatedStringPrimitive expects a bytestring, got {type(data).__name__}')
        if b'\0' in data:
            raise ValueError(f'NullTerminatedStringPrimitive used to encode bytestring containing NULL')
        return len(data)+1, data+b'\0'
    def deserialise(self, raw: bytes) -> tuple[int, tuple[any]]: # consumed, (decoded,)
        if not b'\0' in raw:
            raise IncompleteData()
        data = raw.split(b'\0')[0]
        return len(data)+1, (data,)

cstring = _NullTerminatedStringPrimitive()

class _ArrayPrimitive(_Serialisable):
    def __init__(self, ftype: _Serialisable):
        if ftype == _Serialisable:
            raise ValueError("field in Packet is a raw _Serialisable")
        if not isinstance(ftype, _Serialisable):
            raise ValueError("field in Packet is not a _Serialisable")
        self.type = ftype
    def __repr__(self=None):
        if not self: return f"<Array of Unassigned>"
        return f"<Array of {self.type}>"

    def serialise(self, data: tuple[any]) -> tuple[int, bytes]: # size, raw
        raw = b''
        if len(data) > 1:
            raise ValueError(f'Array expects only a single list of {self.type}, got {len(data)} values')
        data = data[0]
        if not isinstance(data, list):
            raise ValueError(f'Array expects a list of {self.type}, got {type(data).__name__}')
        for elem in data:
            size, serialised = self.type.serialise((elem,))
            raw += serialised # uint32.serialise(size)+serialised
        raw = uint16.serialise((len(data),))[1]+raw
        return len(raw), raw
    def deserialise(self, raw: bytes) -> tuple[int, tuple[any]]: # consumed, (decoded,)
        consumed_total = 0
        cns, (count,) = uint16.deserialise(raw)
        consumed_total, raw = consumed_total + cns, raw[cns:]
        lst = []
        for i in range(count):
            if raw == b'':
                raise IncompleteData()
            cns, (elem,) = self.type.deserialise(raw)
            consumed_total, raw = consumed_total + cns, raw[cns:]
            lst.append(elem)
        return consumed_total, (lst,)

array = _ArrayPrimitive

class _FixedPrimitive(_Serialisable):
    def __init__(self, size: str):
        self.size = size

    def __repr__(self=None):
        if not self: return f"<FixedPrimitive size=?>"
        return f"<FixedPrimitive size={repr(self.size)}>"

    def serialise(self, data: tuple[any]) -> tuple[int, bytes]: # size, raw
        if len(data) > 1:
            raise ValueError(f'FixedPrimitive expects only a single bytestring, got {len(data)} values')
        data = data[0]
        if not isinstance(data, bytes):
            raise ValueError(f'FixedPrimitive expects only a single bytestring, got {type(data).__name__}')
        if len(data) != self.size:
            raise ValueError(f'FixedPrimitive expects only a single bytestring of size {self.size}, got {len(data)}')
        return self.size, data
    def deserialise(self, raw: bytes) -> tuple[int, tuple[any]]: # consumed, (decoded,)
        if len(raw) < self.size:
            raise IncompleteData()
        return self.size, (raw[0:self.size],)

fixed = _FixedPrimitive

class _CStructPrimitiveMeta(type):
    def __new__(cls, clsname, bases, namespace):
        hints = namespace.get("__annotations__", {})
        if annotationlib_Format: # i have no clue why python 3.14 changed that, but now we have to generate annotations and i HATE it
            hints = namespace['__annotate_func__'](1) # (annotationlib_Format.VALUE)

        namespace['_fields'] = []

        for fname, ftype in hints.items():
            if fname.startswith("_"):
                continue
            if ftype == _Serialisable:
                raise ValueError("field in Struct is a raw _Serialisable")
            if not isinstance(ftype, _Serialisable):
                raise ValueError("field in Struct is not a _Serialisable")
            namespace['_fields'].append((fname, ftype))

        # print(f"registering {namespace['__qualname__']} as pid {namespace['_pid']}")

        this = super().__new__(cls, clsname, bases, namespace)

        return this

class _CStructPrimitive(_Serialisable, metaclass=_CStructPrimitiveMeta):
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

    @classmethod
    def serialise(cls, data: tuple[any]) -> tuple[int, bytes]: # size, raw
        # if not self: raise ValueError("StructPrimitive should be initialised")

        if len(data) > 1:
            raise ValueError(f'CStructPrimitive expects only a single struct, got {len(data)} values')
        data = data[0]
        if not isinstance(data, _CStructPrimitive):
            raise ValueError(f'CStructPrimitive expects only a single struct, got {type(data).__name__}')

        raw = b''
        for fname, ftype in data._fields:
            _, ser = ftype.serialise((getattr(data, fname),))
            raw += ser
        return len(raw), raw

    @classmethod
    def deserialise(cls, raw: bytes) -> tuple[int, tuple[any]]: # consumed, (decoded,)
        fields = {}
        cns = 0
        for fname, ftype in cls._fields:
            if raw == b'':
                raise IncompleteData()
            consumed, (decoded,) = ftype.deserialise(raw)
            cns += consumed
            raw = raw[consumed:]
            fields[fname] = decoded
        return cns, (cls(**fields),)

cstruct = _CStructPrimitive