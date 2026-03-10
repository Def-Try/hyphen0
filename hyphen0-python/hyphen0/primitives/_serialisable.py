class _Serialisable:
    def __repr__(self):
        return f"<Serialisable>"

    def serialise(self, *data: any) -> bytes:
        raise ValueError("attempted to use raw _Serialisable")
    def deserialise(self, raw: bytes) -> any:
        raise ValueError("attempted to use raw _Serialisable")