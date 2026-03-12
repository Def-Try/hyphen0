from ._layer import SteganoLayer

class TLSSteganoLayer(SteganoLayer):
    def wrap(self, data: bytes) -> bytes:
        return b"\x17\x03\x03" + len(data).to_bytes(2, 'big', signed=False) + data
    def unwrap(self, data: bytes) -> tuple[int, bytes]:
        assert data[0:3] == b"\x17\x03\x03"
        data_len = int.from_bytes(data[3:5], 'big', signed=False)
        return 5+data_len, data[5:5+data_len]