import asyncio
import random

from dataclasses import dataclass

from protocol.client import Hyphen0Client

from Crypto.PublicKey import ECC

from protocol.packets.chat import ChatUserAuthenticate, ChatUserAdd, ChatUserRemove, ChatUserInfo, \
                                  ChatSendMessage, ChatMessage

@dataclass
class UserInfo:
    username: str

class SimpleChatClient(Hyphen0Client):
    _trace_hooks = False

    def __init__(self, username: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._username = username
        self._userlist = {}
        self._real_username = username
        self._uid = -1

    async def _event_client_connected(self):
        self._socket.write_packet(ChatUserAuthenticate(uinfo=ChatUserInfo(username=self._username.encode())))
        uadd = await self._socket.wait_for_packet(ChatUserAdd)
        self._username = uadd.uinfo.username.decode()
        self._uid = uadd.uid

        self._userlist[self._uid] = UserInfo(username=uadd.uinfo.username.decode())

    async def _event_ptype_ChatUserAdd_received(self, pack: ChatUserAdd):
        self._userlist[pack.uid] = UserInfo(username=pack.uinfo.username.decode())
        await self._call_hook("user_added", pack.uid, self._userlist[pack.uid])
    async def _event_ptype_ChatUserRemove_received(self, pack: ChatUserRemove):
        udata = self._userlist[pack.uid]
        del self._userlist[pack.uid]
        await self._call_hook("user_removed", pack.uid, udata)

    async def _event_ptype_ChatMessage_received(self, pack: ChatMessage):
        await self._call_hook("message_received", pack.uid, self.get_uinfo(pack.uid), pack.content.decode())
    async def _event_ptype_ChatSVMessage_received(self, pack: ChatMessage):
        await self._call_hook("svmessage_received", pack.sender.decode(), pack.content.decode())

    def get_uinfo(self, uid: int):
        return self._userlist.get(uid)

    def send_message(self, content: str):
        self._socket.write_packet(ChatSendMessage(nonce=random.randint(0, 2*32-1), content=content.encode()))
