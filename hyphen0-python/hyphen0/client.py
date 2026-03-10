import asyncio
import functools
import random
import traceback
from .socket.protosocket import ProtoSocket
from .socket.cryptsocket import cast as cast_to_CryptSocket

from .packets.packet import Kick, Disconnect
from .exceptions import WereKicked

from .zerotrust.wrapper import ZerotrustSocket
from .zerotrust.layers.http import HTTPZTLayer

from .packets.handshake import HandshakeInitiate, HandshakeConfirm, HandshakeCancel, HandshakeOK, \
                               HandshakeCryptModesList, HandshakeCryptModeSelect, HandshakeCryptOK, \
                               HandshakeCryptKEXClient, HandshakeCryptKEXServer, \
                               HandshakeCryptTestPing, HandshakeCryptTestPong

from .encryption.aes import AESCrypter

from Crypto.PublicKey import ECC
from Crypto.Protocol import DH
from Crypto.Protocol import KDF
from Crypto.Hash import SHA256

class Hyphen0Client:
    _trace_hooks: bool = True

    ENCRYPTION_MODES = {'aes': AESCrypter}

    def __init__(self, host: str, port: int):
        self._host, self._port = host, port
        self._socket = ZerotrustSocket.cast(ProtoSocket(True), HTTPZTLayer())
        self._keypair = None
        self._session_nonce = None
        self._closed = False
        self._stage = ""
        self._hooks = {}

    def set_keypair(self, keypair):
        if not isinstance(keypair, ECC.EccKey):
            raise ValueError("keypair should be ECCKey")
        self._keypair = keypair

    async def mainloop(self):
        if not self._keypair:
            raise ValueError("set keypair before starting connection")
        self._stage = "connecting"
        try:
            self._socket.connect(self._host, self._port)
        except:
            self._closed = True
            raise
        update_task = asyncio.create_task(self._serve_socket_update())

        self._stage = "handshaking"
        self._socket.write_packet(HandshakeInitiate())
        await self._socket.wait_for_packet(HandshakeConfirm)
        await self._call_hook("client_handshake")

        self._stage = "encrypting_modeset"
        self._socket.write_packet(HandshakeCryptModesList(crypt_modes=[i.encode() for i in self.ENCRYPTION_MODES.keys()]))
        selected_or_cancel = (await self._socket.wait_for_packet([HandshakeCryptModeSelect, HandshakeCancel]))
        if isinstance(selected_or_cancel, HandshakeCancel):
            await self._call_hook("crypt_modeselectfail")
            update_task.cancel()
            self._socket.close()
            self._closed = True
            await self._call_hook("client_killed")
            raise ValueError(f"unable to handshake (server: {selected_or_cancel.message.decode()})")
        # update_task.cancel()

        self._stage = "encrypting_kex"
        selected = selected_or_cancel.crypt_mode.decode()
        await self._call_hook("crypt_modeselected", selected)
        
        kex_server = await self._socket.wait_for_packet(HandshakeCryptKEXServer)
        server_key = ECC.import_key(kex_server.public_key.decode())
        await self._socket._write_packet(HandshakeCryptKEXClient(public_key=self._keypair.public_key().export_key(format='PEM').encode()))
        self._session_nonce = kex_server.salt
        await self._call_hook("crypt_kexok")

        crypter_cls = self.ENCRYPTION_MODES[selected]

        self._stage = "encrypting_start"
        session_key = DH.key_agreement(static_priv=self._keypair, static_pub=server_key, kdf=functools.partial(KDF.HKDF, key_len=kex_server.key_len, salt=self._session_nonce, hashmod=SHA256, num_keys=1, context=b''))
        await self._call_hook("crypt_starting")

        crypter = crypter_cls(session_key)

        await self._socket.wait_for_packet(HandshakeCryptOK)
        
        self._socket = cast_to_CryptSocket(self._socket)
        self._socket.set_encryption(crypter)
        
        self._stage = "encrypting_test"
        test = random.randbytes(512)
        self._socket.write_packet(HandshakeCryptTestPing(test=test))
        if (await self._socket.wait_for_packet(HandshakeCryptTestPong)).test != test:
            await self._call_hook("crypt_testfail")
            self._socket.close()
            self._closed = True
            raise ValueError("unable to handshake (failed at crypttest)")
        self._stage = "encrypting_done"
        await self._call_hook("crypt_complete")
        self._socket.write_packet(HandshakeOK())
        self._update_task = update_task
        await self._call_hook("client_connected")
        self._stage = "running"
        return await self.work()
    def start(self):
        return asyncio.run(self.mainloop())

    async def close(self, message: str = "Disconnect by user", graceful: bool = True):
        if graceful:
            await self._socket._write_packet(Disconnect(message=message.encode()))
        self._update_task.cancel()
        self._update_task = None
        self._socket.close()
        self._closed = True

    async def _serve_socket_update(self):
        while True:
            if self._closed: return
            try:
                await self._socket.update(0)
            except Exception as e:
                print(f'[hyphen0] [LOCAL] {e}')
                print(f"[hyphen0] [LOCAL] recv buffer", self._socket._recv_buffer)
                for line in traceback.format_exc().split('\n'):
                    print(f"[hyphen0] [LOCAL] {line}")
                await self.close(graceful=False)
                raise
            await asyncio.sleep(0)

    def add_hook(self, event: str, name: str, callable):
        self._hooks[event] = self._hooks.get(event, {})
        self._hooks[event][name] = callable

    async def _call_hook(self, event: str, *args, **kwargs):
        if self._trace_hooks:
            print(f"[hyphen0] [LOCAL] {event} {args} {kwargs}")
        for callable in self._hooks.get(event, {}).values():
            await callable(*args, **kwargs)
        if not hasattr(self, f"_event_{event}"):
            return # print(f"[hyphen0] [LOCAL] no hook")
        return await getattr(self, f"_event_{event}")(*args, **kwargs)

    async def work(self):
        while True:
            if self._closed: return
            await asyncio.sleep(0)
            pack = self._socket.read_packet()
            if pack is None: continue
            if isinstance(pack, Kick):
                await self.close(graceful=False)
                raise WereKicked(pack.message.decode())
            await self._call_hook("packet_received", pack)
            await self._call_hook(f"ptype_{type(pack).__name__}_received", pack)