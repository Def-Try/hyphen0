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

async def main_single():
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
    await server.close()
    assert client.connected, "client did not connect"

async def main_multi():
    server = HP0TestServer('', TEST_PORT)
    client1 = HP0TestClient('localhost', TEST_PORT)
    client2 = HP0TestClient('localhost', TEST_PORT)

    server.set_keypair(ECC.generate(curve='p256'))
    client1.set_keypair(ECC.generate(curve='p256'))
    client2.set_keypair(ECC.generate(curve='p256'))

    server_task = asyncio.create_task(server.mainloop())
    client1_task = asyncio.create_task(client1.mainloop())
    client2_task = asyncio.create_task(client2.mainloop())

    start_time = time.time()
    while time.time()-start_time < 1:
        if server_task.done():
            server_exception = server_task.exception()
            if server_exception: raise server_exception
        if client1_task.done():
            client1_exception = client1_task.exception()
            if client1_exception: raise client1_exception
        if client2_task.done():
            client2_exception = client2_task.exception()
            if client2_exception: raise client2_exception
        await asyncio.sleep(0)
        if not client1.connected or not client2.connected:
            continue
        break
    await server.close()
    assert client1.connected, "client1 did not connect"
    assert client2.connected, "client2 did not connect"

def test_svclient_single():
    asyncio.run(main_single())
def test_svclient_multi():
    asyncio.run(main_multi())