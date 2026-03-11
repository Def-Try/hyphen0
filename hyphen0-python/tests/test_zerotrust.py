import asyncio
import time
import random

from hyphen0.socket import ProtoSocket, CryptSocket
from hyphen0.packets import Packet, pack
from hyphen0.server import Hyphen0Server
from hyphen0.client import Hyphen0Client
from hyphen0.stegano.http import HTTPSteganoLayer

from Crypto.PublicKey import ECC

TEST_PORT = 1340 # random.randint(1024, 65535)
TEST_STRING = b"hello, world!"

class PacketTestServerbound(Packet):
    _serverbound: bool = True

    string: pack.cstring # type: ignore

class PacketTestClientbound(Packet):
    _serverbound: bool = False

    string: pack.cstring # type: ignore

async def main_sockets():
    server_host_socket = ProtoSocket(False, 1, 5, HTTPSteganoLayer())
    client_host_socket = ProtoSocket(True,  1, 5, HTTPSteganoLayer())

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

async def main_svclient():
    server = HP0TestServer('', TEST_PORT, HTTPSteganoLayer())
    client = HP0TestClient('localhost', TEST_PORT, HTTPSteganoLayer())

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

def test_zerotrust_sockets():
    asyncio.run(main_sockets())
def test_zerotrust_svclient():
    asyncio.run(main_svclient())