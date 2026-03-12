import asyncio
import random

from hyphen0.socket import ProtoSocket, CryptSocket
from hyphen0.packets import Packet, pack
from hyphen0.stegano import HTTPSteganoLayer
from hyphen0.encryption.aes import AESCrypter

from Crypto.PublicKey import ECC

TEST_PORT = 1340 # random.randint(1024, 65535)
TEST_KEY = b"0123456789012345"
TEST_STRING = b"hello, world!"

class PacketTestServerbound(Packet):
    _serverbound: bool = True

    string: pack.cstring # type: ignore

class PacketTestClientbound(Packet):
    _serverbound: bool = False

    string: pack.cstring # type: ignore

async def main_protosocket():
    server_host_socket = ProtoSocket(False, 1, 5)
    client_host_socket = ProtoSocket(True,  1, 5)

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

async def main_protosocket_stegano():
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

async def main_cryptsocket():
    server_crypter, client_crypter = AESCrypter(TEST_KEY), AESCrypter(TEST_KEY)
    server_host_socket = ProtoSocket(False, 1, 5)
    client_host_socket = CryptSocket(ProtoSocket(True,  1, 5))

    server_host_socket.bind("", TEST_PORT, 1)
    client_host_socket.connect("127.0.0.1", TEST_PORT)
    server_peer_socket, server_peer_address = await server_host_socket.accept()

    server_peer_socket = CryptSocket(server_peer_socket)
    server_peer_socket.set_encryption(server_crypter)
    client_host_socket.set_encryption(client_crypter)

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

async def main_cryptsocket_stegano():
    server_crypter, client_crypter = AESCrypter(TEST_KEY), AESCrypter(TEST_KEY)
    server_host_socket = ProtoSocket(False, 1, 5, HTTPSteganoLayer())
    client_host_socket = CryptSocket(ProtoSocket(True,  1, 5, HTTPSteganoLayer()))

    server_host_socket.bind("", TEST_PORT, 1)
    client_host_socket.connect("127.0.0.1", TEST_PORT)
    server_peer_socket, server_peer_address = await server_host_socket.accept()

    server_peer_socket = CryptSocket(server_peer_socket)
    server_peer_socket.set_encryption(server_crypter)
    client_host_socket.set_encryption(client_crypter)

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

def test_protosocket(): asyncio.run(main_protosocket())
def test_protosocket_stegano(): asyncio.run(main_protosocket_stegano())
def test_cryptsocket(): asyncio.run(main_cryptsocket())
def test_cryptsocket_stegano(): asyncio.run(main_cryptsocket_stegano())