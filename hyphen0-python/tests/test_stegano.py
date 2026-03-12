import asyncio
import time
import random

from hyphen0.socket import ProtoSocket, CryptSocket
from hyphen0.packets import Packet, pack
from hyphen0.server import Hyphen0Server
from hyphen0.client import Hyphen0Client
from hyphen0.stegano import TLSSteganoLayer

from Crypto.PublicKey import ECC

TEST_PORT = random.randint(1024, 65535)
TEST_STRING = b"hello, world!"

class PacketTestServerbound(Packet):
    _serverbound: bool = True

    string: pack.cstring # type: ignore

class PacketTestClientbound(Packet):
    _serverbound: bool = False

    string: pack.cstring # type: ignore

async def main_sockets():
    server_host_socket = ProtoSocket(False, 1, 5, TLSSteganoLayer())
    client_host_socket = ProtoSocket(True,  1, 5, TLSSteganoLayer())

    server_host_socket.bind("", TEST_PORT, 1)
    client_host_socket.connect("127.0.0.1", TEST_PORT)
    server_peer_socket, server_peer_address = await server_host_socket.accept()

    server_packet = PacketTestClientbound(string=TEST_STRING)
    server_peer_socket.write_packet(server_packet)
    await server_peer_socket.update(0) # send packet

    await client_host_socket.update(0) # receive packet
    received_client_packet = client_host_socket.read_packet()
    assert isinstance(received_client_packet, PacketTestClientbound)
    assert received_client_packet.string == TEST_STRING

    client_packet = PacketTestServerbound(string=TEST_STRING)
    client_host_socket.write_packet(client_packet)
    await client_host_socket.update(0) # send packet

    await server_peer_socket.update(0) # receive packet
    received_server_packet = server_peer_socket.read_packet()
    assert isinstance(received_server_packet, PacketTestServerbound)
    assert received_server_packet.string == TEST_STRING

    client_host_socket.close()
    server_peer_socket.close()
    server_host_socket.close()

class HP0TestServer(Hyphen0Server):
    _capture_errors: bool = False
class HP0TestClient(Hyphen0Client):
    _capture_errors: bool = False
    connected = False
    async def _event_client_connected(self):
        self.connected = True

async def main_svclient_single():
    server = HP0TestServer('', TEST_PORT, TLSSteganoLayer())
    client = HP0TestClient('localhost', TEST_PORT, TLSSteganoLayer())

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

async def main_svclient_multi():
    server = HP0TestServer('', TEST_PORT, TLSSteganoLayer())
    client1 = HP0TestClient('localhost', TEST_PORT, TLSSteganoLayer())
    client2 = HP0TestClient('localhost', TEST_PORT, TLSSteganoLayer())

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

def test_zerotrust_sockets():
    asyncio.run(main_sockets())
def test_zerotrust_svclient_single():
    asyncio.run(main_svclient_single())
def test_zerotrust_svclient_multi():
    asyncio.run(main_svclient_multi())