import random
import string

from .._layer import ZTLayer

class HTTPZTLayer(ZTLayer):
    def _randomstr(self):
        return ''.join(string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)] for i in range(random.randint(16, 32)))
    def _useragent(self):
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
    
    def _make_header(self) -> bytes:
        return b"GET /"+self._randomstr().encode()+b" HTTP/1.1\nConnection: keep-alive\nCache-Control: max-age=0\nUser-Agent: "+self._useragent().encode()+b"\nAccept: */*\n"
    def _parse_header(self, data) -> tuple[int, int]:
        assert(data[0:5] == b"GET /")
        return data.index(b"\n\n")+2, int(data[data.index(b"Content-Length: ")+16:data.index(b"\n\n")].decode())

    def wrap(self, data: bytes) -> bytes:
        return self._make_header()+b"Content-Length: "+str(len(data)).encode()+b"\n\n"+data
    def unwrap(self, data: bytes) -> tuple[int, bytes]:
        skip_header, data_size = self._parse_header(data)
        return skip_header+data_size, data[skip_header:skip_header+data_size]
