import asyncio

from protocol.socket.protosocket import ProtoSocket
from protocol.socket.cryptsocket import CryptSocket
from protocol.packets.chat import ChatSendMessage, ChatMessage


from protocol.encryption.aes256 import AES256Crypter

async def main():
    # basicsockets are sockets that automatically handle being randomly closed
    # protosockets are basicsockets that also send packets instead of raw data and have a thread-safe way to do so
    server, client = ProtoSocket(False), ProtoSocket(True)
    server.bind('127.0.0.1', 12345)
    client.connect('127.0.0.1', 12345)

    print("SERVER: accept client")
    # we still have to accept clients for now, duuh
    svside_client, _ = await server.accept()
    # svside_client is now a ProtoSocket associated with just connected client
    # for clarity in this example lets also name our client clside_client
    clside_client = client

    print("CLIENT: send ChatSendMessage")
    # let's try "sending" a client message to server and "receiving" it on server
    # .write_packet(packet: Packet) adds a packet to sending queue
    clside_client.write_packet(ChatSendMessage(content=b"whoops i gilbed"))
    # .update(timeout: float) updates protosocket. sending and receiving one packet from the queue
    # ideally it must be run every 1/60th of a second in a dedicated thread
    await clside_client.update(0)

    print("SERVER: receive packet")
    # client sent us a packet, let's accept it on server
    # call the .update on serverside
    await svside_client.update(0)
    # and read one packet from the queue
    # .read_packet() -> packet: Packet pops a packet from receiving queue
    svside_recv = svside_client.read_packet()
    print('SERVER: received packet', svside_recv)
    # and maybe send a reply!

    # but we want to encrypt our traffic, so lets do that!
    # ideally you'll create this Crypter using some kind of key exchange like DH or physically giving passowrds to user
    crypter = AES256Crypter(b'testtesttesttest')

    print("SERVER: starting encryption")
    # we need to turn our ProtoSockets into ones that support encryption
    # CryptSocket is an abstraction over ProtoSocket that you need to "cast" protosocket to
    # that retains all it's data and basically doesn't change it
    svside_client = CryptSocket.cast(svside_client)
    # and then we set it's encryption to the generated crypter
    svside_client.set_encryption(crypter)

    print("CLIENT: starting encryption")
    # same process here, but on client
    clside_client = CryptSocket.cast(clside_client)
    clside_client.set_encryption(crypter)

    print("SERVER: send ChatMessage")
    # write to queue
    svside_client.write_packet(ChatMessage(user_name=b"Gilber", content=b"whoops i gilbed"))
    # update and send
    await svside_client.update(0)

    print("CLIENT: receive packet")
    # update and receive
    await clside_client.update(0)
    # read from queue
    clside_recvd = client.read_packet()
    print('CLIENT: received packet', clside_recvd)


if __name__ == "__main__":
    asyncio.run(main())
