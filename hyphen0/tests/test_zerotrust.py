import asyncio

from hyphen0.socket.protosocket import ProtoSocket
from hyphen0.packets.handshake import HandshakeInitiate, HandshakeConfirm

from hyphen0.zerotrust.wrapper import ZerotrustSocket
from hyphen0.zerotrust.layers.http import HTTPZTLayer

async def main():
    server_socket = ZerotrustSocket.cast(ProtoSocket(False, 10, 5), HTTPZTLayer())
    server_socket.bind("", 1337, 8)

    client_socket = ZerotrustSocket.cast(ProtoSocket(True, 10, 5), HTTPZTLayer())
    client_socket.connect("localhost", 1337)

    server_client_socket, _ = await server_socket.accept()
    # server_client_socket = ZerotrustSocket.cast(server_client_socket, HTTPZTLayer())

    for i in range(10):
        client_socket.write_packet(HandshakeInitiate())
        await client_socket.update(0)
        await server_client_socket.update(0)
        print(server_client_socket.read_packet())
        server_client_socket.write_packet(HandshakeConfirm())
        await server_client_socket.update(0)
        await client_socket.update(0)
        print(client_socket.read_packet())

def run():
    print("--- test zerotrust ---")
    asyncio.run(main())