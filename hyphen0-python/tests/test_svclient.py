import asyncio
import time
import random

from hyphen0.server import Hyphen0Server
from hyphen0.client import Hyphen0Client

from Crypto.PublicKey import ECC

TEST_PORT = random.randint(1024, 65535)

class HP0TestServer(Hyphen0Server):
    pass
class HP0TestClient(Hyphen0Client):
    connected = False
    async def _event_client_connected(self):
        self.connected = True

async def main():
    server = HP0TestServer('', TEST_PORT)
    client = HP0TestClient('localhost', TEST_PORT)

    server.set_keypair(ECC.generate(curve='p256'))
    client.set_keypair(ECC.generate(curve='p256'))

    server_task = asyncio.create_task(server.mainloop())
    client_task = asyncio.create_task(client.mainloop())

    start_time = time.time()
    while time.time()-start_time < 1:
        if server_task.done():
            server_exception = server_task.exception()
            if server_exception: raise server_exception
        if client_task.done():
            client_exception = client_task.exception()
            if client_exception: raise client_exception
        await asyncio.sleep(0)
        if not client.connected:
            continue
        break
    assert client.connected, "client did not connect"

def test_svclient():
    asyncio.run(main())