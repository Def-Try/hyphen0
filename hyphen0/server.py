import asyncio
import random

from protocol.server import Hyphen0Server
from protocol.client import Hyphen0Client

from Crypto.PublicKey import ECC

from protocol.packets.chat import ChatUserAuthenticate, ChatUserAdd, ChatUserRemove, ChatUserInfo, \
                                  ChatSendMessage, ChatMessage, ChatSVMessage

class SimpleChatServer(Hyphen0Server):
    _trace_hooks = False
    _motd = '\n'.join(i.strip() for i in ("""
        Welcome to the Demo Server
        This is just a simple End-2-end encrypted chat, HOWEVER protocol can be expanded to send arbitrary data
    """).split("\n")).strip()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.free_uids = list(range(0, 256))
    async def _event_client_connected(self, client: ProtoSocket):
        print("[SERVER] new client, waiting for register packet")
        authpack = await client.wait_for_packet(ChatUserAuthenticate)
        print("[SERVER] registering")
        if len(self.free_uids) == 0:
            await self.kick_client(client, "no more free user ids", True)
            raise ValueError("no more free uids")
        cldata = self.get_client_data(client)
        cldata['uinfo'] = authpack.uinfo
        cldata['uid'] = self.free_uids.pop(0)
        client.write_packet(ChatUserAdd(uid=cldata['uid'], uinfo=cldata['uinfo']))
        for broadcast_client in self.get_clients():
            bcldata = self.get_client_data(broadcast_client)
            if 'uid' not in bcldata: continue
            broadcast_client.write_packet(ChatUserAdd(uid=cldata['uid'], uinfo=cldata['uinfo']))
            # if bcldata['uid'] == cldata['uid']: continue
            client.write_packet(ChatUserAdd(uid=bcldata['uid'], uinfo=bcldata['uinfo']))
        client.write_packet(ChatSVMessage(sender=b"MOTD", content=self._motd.encode()))
        print("[SERVER] registered")
    async def _event_client_disconnecting(self, client: ProtoSocket):
        print("[SERVER] client left")
        cldata = self.get_client_data(client)
        self.free_uids.append(cldata['uid'])
        uid = cldata['uid']
        del cldata['uid']
        for broadcast_client in self.get_clients():
            bcldata = self.get_client_data(broadcast_client)
            if 'uid' not in bcldata: continue
            broadcast_client.write_packet(ChatUserRemove(uid=uid))

    async def _event_ptype_ChatSendMessage_received(self, client: ProtoSocket, pack: ChatSendMessage):
        cldata = self.get_client_data(client)
        if 'uid' not in cldata: return
        print(f"[SERVER] received message from {cldata['uinfo'].username.decode()}: \"{pack.content.decode()}\", broadcasting")
        for broadcast_client in self.get_clients():
            bcldata = self.get_client_data(broadcast_client)
            if 'uid' not in bcldata: continue
            broadcast_client.write_packet(ChatMessage(uid=cldata['uid'], content=pack.content, nonce=pack.nonce))

server = SimpleChatServer('', 12345)
server.set_keypair(ECC.generate(curve='p256'))

server.serve()