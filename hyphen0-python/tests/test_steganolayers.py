from hyphen0.stegano.http import HTTPSteganoLayer


def test_steganolayer_http():
    testsend = HTTPSteganoLayer()
    testrecv = HTTPSteganoLayer()
    testsend.set_serverbound(True)
    testrecv.set_serverbound(False)
    testsend.set_url("testtesttest")
    testrecv.set_url("testtesttest")
    testsend._useragent_str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
    testrecv._useragent_str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"

    testsend.push_send(b"helloworld")
    pulled1 = testsend.pull_send(5)
    pulled2 = testsend.pull_send(5)
    assert pulled1 == b'POST /testtesttest HTTP/1.1\nConnection: keep-alive\nCache-Control: max-age=0\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0\nAccept: */*\nContent-Length: 8\n\naGVsbG8='
    assert pulled2 == b'POST /testtesttest HTTP/1.1\nConnection: keep-alive\nCache-Control: max-age=0\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0\nAccept: */*\nContent-Length: 8\n\nd29ybGQ='

    testrecv.push_recv(pulled1)
    testrecv.push_recv(pulled2)
    assert testrecv.pull_recv(5) == b"hello"
    assert testrecv.pull_recv(5) == b"world"