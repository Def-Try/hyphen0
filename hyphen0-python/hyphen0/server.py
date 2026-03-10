import asyncio
import random
import functools
import traceback
from .socket.protosocket import ProtoSocket
from .socket.cryptsocket import cast as cast_to_CryptSocket

from .packets.packet import Kick, Disconnect
from .exceptions import WereDisconnected, SocketClosed

from .zerotrust.wrapper import ZerotrustSocket
from .zerotrust.layers.http import HTTPZTLayer

from .packets.handshake import HandshakeInitiate, HandshakeConfirm, HandshakeCancel, HandshakeOK, \
                               HandshakeCryptModesList, HandshakeCryptModeSelect, HandshakeCryptOK, \
                               HandshakeCryptKEXClient, HandshakeCryptKEXServer, \
                               HandshakeCryptTestPing, HandshakeCryptTestPong

from .encryption.aes import AESCrypter

from Crypto.Random import get_random_bytes
from Crypto.PublicKey import ECC
from Crypto.Protocol import DH
from Crypto.Protocol import KDF
from Crypto.Hash import SHA256

class Hyphen0Server:
    _trace_hooks: bool = True

    ENCRYPTION_MODES = {'aes': AESCrypter}

    KEY_LENGTH = 32

    def __init__(self, host: str, port: int):
        self._host, self._port = host, port
        self._socket = ZerotrustSocket.cast(ProtoSocket(False), HTTPZTLayer())
        self._socket.bind(host, port)
        self._keypair = None
        self._session_nonce = get_random_bytes(32)
        self._connected_clients = {}

    def set_keypair(self, keypair):
        if not isinstance(keypair, ECC.EccKey):
            raise ValueError("keypair should be ECCKey")
        self._keypair = keypair

    async def mainloop(self):
        if not self._keypair:
            raise ValueError("set keypair before starting connection")
        print(f"[hyphen0] serving on {self._host}:{self._port}")
        while True:
            client, addr = await self._socket.accept()
            print(f"[hyphen0] new client connected: {addr[0]}:{addr[1]}")
            asyncio.create_task(self._client_connected(client))

    def serve(self):
        return asyncio.run(self.mainloop())
    
    async def _client_connected(self, client: ProtoSocket):
        update_task = asyncio.create_task(self._serve_client_update(client))
        await client.wait_for_packet(HandshakeInitiate)
        client.write_packet(HandshakeConfirm())
        await self._call_hook(client, "client_handshake")

        modeslist = (await client.wait_for_packet(HandshakeCryptModesList)).crypt_modes
        shared_modes = [i.decode() for i in (set([i.encode() for i in self.ENCRYPTION_MODES.keys()]) & set(modeslist))]
        if len(shared_modes) == 0:
            await self._call_hook(client, "crypt_modeselectfail")
            update_task.cancel()
            await client._write_packet(HandshakeCancel(message=b'no shared encryption modes found'))
            await self._call_hook(client, "client_killed")
            client.close()
            return
        await self._call_hook(client, "crypt_modeselected", shared_modes[0])
        client.write_packet(HandshakeCryptModeSelect(crypt_mode=shared_modes[0].encode()))
        # update_task.cancel()
        
        client.write_packet(HandshakeCryptKEXServer(salt=self._session_nonce,
                                                    key_len=self.KEY_LENGTH,
                                                    public_key=self._keypair.public_key().export_key(format='PEM').encode()))
        kex_client = await client.wait_for_packet(HandshakeCryptKEXClient)
        client_key = ECC.import_key(kex_client.public_key.decode())
        await self._call_hook(client, "crypt_kexok")

        crypter_cls = self.ENCRYPTION_MODES[shared_modes[0]]

        session_key = DH.key_agreement(static_priv=self._keypair, static_pub=client_key, kdf=functools.partial(KDF.HKDF, key_len=self.KEY_LENGTH, salt=self._session_nonce, hashmod=SHA256, num_keys=1, context=b''))
        await self._call_hook(client, "crypt_starting")

        await client._write_packet(HandshakeCryptOK())

        crypter = crypter_cls(session_key)
        client = cast_to_CryptSocket(client)
        client.set_encryption(crypter)

        test = (await client.wait_for_packet(HandshakeCryptTestPing)).test
        client.write_packet(HandshakeCryptTestPong(test=test))

        if type(await client.wait_for_packet(HandshakeOK)) != HandshakeOK:
            await self._call_hook(client, "crypt_testfail")
            update_task.cancel()
            client.close()
            return
        await self._call_hook(client, "crypt_complete")
        self._connected_clients[client.getnicename()] = {'upd': update_task, 'sock': client}
        await self._call_hook(client, "client_connected")
        return await self.work(client)

    async def _serve_client_update(self, client: ProtoSocket):
        while True:
            try:
                await client.update(0)
            except SocketClosed:
                print(f"[hyphen0] [{client.getnicename()}] connection terminated")
                return await self.kick_client(client, graceful=False)
            except Exception as e:
                print(f'[hyphen0] [{client.getnicename()}] {e}')
                print(f"[hyphen0] [{client.getnicename()}] recv buffer", self._socket._recv_buffer)
                for line in traceback.format_exc().split('\n'):
                    print(f"[hyphen0] [{client.getnicename()}] {line}")
                await self.kick_client(client, graceful=False)
                raise
            await asyncio.sleep(0)

    def get_client_data(self, client: ProtoSocket) -> dict:
        return self._connected_clients.get(client.getnicename())
    def get_clients(self) -> list[ProtoSocket]:
        return [dct['sock'] for dct in self._connected_clients.values()]

    async def kick_client(self, client: ProtoSocket, message: str = "Kicked by server", graceful: bool = True):
        await self._call_hook(client, "client_disconnecting")
        if graceful:
            await client._write_packet(Kick(message=message.encode()))
        self._connected_clients[client.getnicename()]['upd'].cancel()
        del self._connected_clients[client.getnicename()]
        client.close()

    async def _call_hook(self, client: ProtoSocket, event: str, *args, **kwargs):
        if self._trace_hooks:
            print(f"[hyphen0] [{'LOCAL' if not client else client.getnicename()}] {event} {args} {kwargs}")
        if not hasattr(self, f"_event_{event}"):
            return # print(f"[hyphen0] [{'LOCAL' if not client else client.getnicename()}] no hook")
        return await getattr(self, f"_event_{event}")(client, *args, **kwargs)

    async def work(self, client: ProtoSocket):
        while True:
            if not client.getnicename() in self._connected_clients:
                return print(f"[hyphen0] [{client.getnicename()}] client disappeared, bailing out")
            await asyncio.sleep(0)

            pack = client.read_packet()
            if pack is None: continue
            if isinstance(pack, Disconnect):
                nicename = client.getnicename()
                await self.kick_client(client, graceful=False)
                raise WereDisconnected(nicename+": "+pack.message.decode())
            await self._call_hook(client, "packet_received", pack)
            await self._call_hook(client, f"ptype_{type(pack).__name__}_received", pack)