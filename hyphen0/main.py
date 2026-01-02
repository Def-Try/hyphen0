import asyncio
import random

from hyphen0.server import Hyphen0Server
from hyphen0.client import Hyphen0Client

from Crypto.PublicKey import ECC

from hyphen0.packets.chat import ChatUserAuthenticate, ChatUserAdd, ChatUserRemove, ChatUserInfo, \
                                  ChatSendMessage, ChatMessage

class SimpleChatClient(Hyphen0Client):
    _trace_hooks = True

    def __init__(self, username: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._username = username
        self._userlist = {}
        self._real_username = username
        self._uid = -1

    async def _event_client_connected(self):
        print(f"[CLIENT] registering as {self._username}")
        self._socket.write_packet(ChatUserAuthenticate(uinfo=ChatUserInfo(username=self._username.encode())))
        print("[CLIENT] waiting for server to confirm")
        uadd = await self._socket.wait_for_packet(ChatUserAdd)
        print(f"[CLIENT] registered as {uadd.uinfo.username.decode()} UID={uadd.uid}")

        print("[CLIENT] send message: \"hiiiii\"")
        self.send_message("hiiiii")

    async def _event_ptype_ChatUserAdd_received(self, pack: ChatUserAdd):
        await self._call_hook("user_added", pack.uid)
    async def _event_ptype_ChatUserRemove_received(self, pack: ChatUserRemove):
        await self._call_hook("user_removed", pack.uid)

    async def _event_ptype_ChatMessage_received(self, pack: ChatMessage):
        await self._call_hook("message_received", pack.uid, pack.content.decode())
    async def _event_ptype_ChatSVMessage_received(self, pack: ChatMessage):
        await self._call_hook("svmessage_received", pack.sender.decode(), pack.content.decode())

    def send_message(self, content: str):
        self._socket.write_packet(ChatSendMessage(nonce=random.randint(0, 2*32-1), content=content.encode()))

class SimpleChatServer(Hyphen0Server):
    _trace_hooks = False
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
            if bcldata['uid'] == cldata['uid']: continue
            client.write_packet(ChatUserAdd(uid=bcldata['uid'], uinfo=bcldata['uinfo']))
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


async def main():
    server = SimpleChatServer('', 12345)
    client1 = SimpleChatClient('testuser1', '127.0.0.1', 12345)
    client2 = SimpleChatClient('testuser2', '127.0.0.1', 12345)

    server.set_keypair(ECC.generate(curve='p256'))
    client1.set_keypair(ECC.generate(curve='p256'))
    client2.set_keypair(ECC.generate(curve='p256'))

    # client.start()
    # server.serve()

    asyncio.create_task(server.mainloop())
    await asyncio.sleep(0.1)
    asyncio.create_task(client1.mainloop())
    await asyncio.sleep(0.1)
    asyncio.create_task(client2.mainloop())
    await asyncio.sleep(3)
    await client2.close()
    await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())