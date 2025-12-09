import asyncio
import random
from .socket.protosocket import ProtoSocket
from .socket.cryptsocket import CryptSocket

from .packets.handshake import HandshakeInitiate, HandshakeConfirm, HandshakeCancel, HandshakeOK, \
                               HandshakeCryptModesList, HandshakeCryptModeSelect, HandshakeCryptOK, \
                               HandshakeCryptKEXClient, HandshakeCryptKEXServer, \
                               HandshakeCryptTestPing, HandshakeCryptTestPong

from .encryption.aes256 import AES256Crypter

class Hyphen0Client:
    ENCRYPTION_MODES = {'aes256': AES256Crypter}

    def __init__(self, host: str, port: int):
        self._host, self._port = host, port
        self._socket = ProtoSocket(True)

    async def mainloop(self):
        self._socket.connect(self._host, self._port)
        update_task = asyncio.create_task(self._serve_socket_update())

        self._socket.write_packet(HandshakeInitiate())
        await self._socket.wait_for_packet(HandshakeConfirm)
        
        self._socket.write_packet(HandshakeCryptModesList(crypt_modes=[i.encode() for i in self.ENCRYPTION_MODES.keys()]))
        selected_or_cancel = (await self._socket.wait_for_packet([HandshakeCryptModeSelect, HandshakeCancel]))
        if isinstance(selected_or_cancel, HandshakeCancel):
            update_task.cancel()
            self._socket.close()
            raise ValueError(f"unable to handshake (server: {selected_or_cancel.message.decode()})")
        await self._socket._write_packet(HandshakeCryptOK())
        # update_task.cancel()
        
        selected = selected_or_cancel.crypt_mode.decode()
        # key exchange magic here
        shared_key = b' test test test '
        crypter = self.ENCRYPTION_MODES[selected](shared_key)
        
        self._socket = CryptSocket.cast(self._socket)
        self._socket.set_encryption(crypter)
        
        test = random.randbytes(512)
        self._socket.write_packet(HandshakeCryptTestPing(test=test))
        if (await self._socket.wait_for_packet(HandshakeCryptTestPong)).test != test:
            self._socket.close()
            raise ValueError("unable to handshake (failed at crypttest)")
        self._socket.write_packet(HandshakeOK())
        print("CL handshake complete!")
        await asyncio.sleep(1)
    def start(self):
        return asyncio.run(self.mainloop())

    async def _serve_socket_update(self):
        while True:
            try:
                await self._socket.update(0)
            except Exception as e:
                print(f'[hyphen0] {e}')
                self._socket._close()
                return False
            await asyncio.sleep(0)