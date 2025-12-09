import asyncio
import random
from .socket.protosocket import ProtoSocket
from .socket.cryptsocket import CryptSocket

from .packets.handshake import HandshakeInitiate, HandshakeConfirm, HandshakeCancel, HandshakeOK, \
                               HandshakeCryptModesList, HandshakeCryptModeSelect, HandshakeCryptOK, \
                               HandshakeCryptKEXClient, HandshakeCryptKEXServer, \
                               HandshakeCryptTestPing, HandshakeCryptTestPong

from .encryption.aes256 import AES256Crypter

class Hyphen0Server:
    ENCRYPTION_MODES = {'aes256': AES256Crypter}

    def __init__(self, host: str, port: int):
        self._host, self._port = host, port
        self._socket = ProtoSocket(False)
        self._socket.bind(host, port)

    async def mainloop(self):
        print(f"[hyphen0] serving on {self._host}:{self._port}")
        while True:
            client, addr = await self._socket.accept()
            print(f"[hyphen0] new client connected: {addr[0]}:{addr[1]}")
            await self._client_connected(client)

    def serve(self):
        return asyncio.run(self.mainloop())
    
    async def _client_connected(self, client: ProtoSocket):
        update_task = asyncio.create_task(self._serve_client_update(client))
        await client.wait_for_packet(HandshakeInitiate)
        client.write_packet(HandshakeConfirm())

        modeslist = (await client.wait_for_packet(HandshakeCryptModesList)).crypt_modes
        shared_modes = [i.decode() for i in (set([i.encode() for i in self.ENCRYPTION_MODES.keys()]) & set(modeslist))]
        if len(shared_modes) == 0:
            update_task.cancel()
            await client._write_packet(HandshakeCancel(message=b'no shared encryption modes found'))
            client.close()
            return
        await client._write_packet(HandshakeCryptModeSelect(crypt_mode=shared_modes[0].encode()))
        await client.wait_for_packet(HandshakeCryptOK)
        # update_task.cancel()
        
        # key exchange magic here
        shared_key = b' test test test '
        crypter = self.ENCRYPTION_MODES[shared_modes[0]](shared_key)
        client = CryptSocket.cast(client)
        client.set_encryption(crypter)

        test = (await client.wait_for_packet(HandshakeCryptTestPing)).test
        client.write_packet(HandshakeCryptTestPong(test=test))

        if type(await client.wait_for_packet(HandshakeOK)) != HandshakeOK:
            print("handshake not ok")
            update_task.cancel()
            client.close()
            return
        print("SV handshake ok!")

    async def _serve_client_update(self, client: ProtoSocket):
        while True:
            try:
                await client.update(0)
            except Exception as e:
                print(f'[hyphen0] {e}')
                client._close()
                return False
            await asyncio.sleep(0)