import random
import string

import base64
import ua_generator

from .._layer import ZTLayer

class HTTPZTLayer(ZTLayer):
    _useragent_str: str = None
    def _randomstr(self):
        return ''.join(string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)] for i in range(random.randint(16, 32)))
    def _useragent(self):
        if not self._useragent_str:
            self._useragent_str = ua_generator.generate().text
        return self._useragent_str
    
    def _make_header(self) -> bytes:
        return b"POST /"+self._randomstr().encode()+b" HTTP/1.1\nConnection: keep-alive\nCache-Control: max-age=0\nUser-Agent: "+self._useragent().encode()+b"\nAccept: */*\n"
    def _parse_header(self, data) -> tuple[int, int]:
        assert(data[0:6] == b"POST /")
        return data.index(b"\n\n")+2, int(data[data.index(b"Content-Length: ")+16:data.index(b"\n\n")].decode())

    def wrap(self, data: bytes) -> bytes:
        data = base64.b64encode(data)
        return self._make_header()+b"Content-Length: "+str(len(data)).encode()+b"\n\n"+data
    def unwrap(self, data: bytes) -> tuple[int, bytes]:
        skip_header, data_size = self._parse_header(data)
        return skip_header+data_size, base64.b64decode(data[skip_header:skip_header+data_size])
