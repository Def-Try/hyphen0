import random
import string

import base64
import ua_generator

from ._layer import SteganoLayer

class HTTPSteganoLayer(SteganoLayer):
    _useragent_str: str = None
    _url: str = None
    def set_url(self, url: str = None): self._url = url
    def _randomstr(self):
        return ''.join(string.ascii_letters[random.randint(0, len(string.ascii_letters)-1)] for i in range(random.randint(16, 32)))
    def _useragent(self):
        if not self._useragent_str:
            self._useragent_str = ua_generator.generate().text
        return self._useragent_str
    
    def _make_header(self) -> bytes:
        if self.serverbound:
            return b"POST /"+(self._randomstr() if self._url is None else self._url).encode()+b" HTTP/1.1\nConnection: keep-alive\nCache-Control: max-age=0\nUser-Agent: "+self._useragent().encode()+b"\nAccept: */*\n"
        return b"HTTP/1.1 200 OK\nConnection: keep-alive\nCache-Control: max-age=0\n"
    def _parse_header(self, data) -> tuple[int, int]:
        if self.serverbound: # server -> client
            assert(data[0:15] == b"HTTP/1.1 200 OK")
            return data.index(b"\n\n")+2, int(data[data.index(b"Content-Length: ")+16:data.index(b"\n\n")].decode())
        assert(data[0:6] == b"POST /")
        end = data.index(b"\n\n")+2
        length = int(data[data.index(b"Content-Length: ")+16:end].decode())
        return end, length

    def wrap(self, data: bytes) -> bytes:
        data = base64.b64encode(data)
        return self._make_header()+b"Content-Length: "+str(len(data)).encode()+b"\n\n"+data
    def unwrap(self, data: bytes) -> tuple[int, bytes]:
        skip_header, data_size = self._parse_header(data)
        return skip_header+data_size, base64.b64decode(data[skip_header:skip_header+data_size])