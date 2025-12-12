import asyncio
import random

from Crypto.PublicKey import ECC

from textual import on
from textual.app import App
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, Static, Input
from pathlib import Path

from .client import SimpleChatClient

from .screens.connect import ConnectScreen

from .widgets.message import Message

class Hyphen0ChatClientApp(App):
    DEFAULT_CSS = """
    #messages-container {
        background: #222222;
        height: 0.8fr;
    }
    #message-input {
        height: 0.2fr;
    }
    """

    def __init__(self):
        super().__init__()

        self.client = None

    def on_mount(self):
        self.open_connect_screen()
    def open_connect_screen(self):
        self.add_message("SYSTEM", "opening connection dialog")
        self.push_screen(ConnectScreen(self))

    def compose(self):
        yield Header()
        with ScrollableContainer(id="messages-container"):
            pass
        yield Input(placeholder="Send...", id="message-input")
        yield Footer()

    def add_message(self, sender, content):
        container = self.query_one("#messages-container")
        should_scroll = (container.max_scroll_y - container.scroll_target_y) <= 5
        container.mount(Message(sender, content))
        if should_scroll:
            container.scroll_end(animate=False)

    @on(Input.Submitted, "#message-input")
    def send_message_event(self, event):
        event.control.clear()
        if not self.client: return
        self.client.send_message(event.value)

    def _complete_client(self):
        self.client.add_hook("message_received", "receive_messages", self._precv_chat_message)
        self.client.add_hook("svmessage_received", "receive_messages", self._precv_svchat_message)
        self.client.add_hook("user_added", "users_change", self._precv_uch_add)
        self.client.add_hook("user_removed", "users_change", self._precv_uch_remove)
    async def _precv_chat_message(self, uid, uinfo, content):
        self.add_message(uinfo.username, content)
    async def _precv_svchat_message(self, sender, content):
        self.add_message(sender, content)
    async def _precv_uch_add(self, uid, uinfo):
        self.add_message("SYSTEM", f"\\+ {uinfo.username} joined")
    async def _precv_uch_remove(self, uid, uinfo):
        self.add_message("SYSTEM", f"\\- {uinfo.username} left")


    async def attempt_connecting(self, uname: str, address: str):
        if not address.startswith("hyph0://"):
            yield False, "address should be in form 'hyph0://[host]:[port]' ('hyph0://' not found)"
        address = address[8:]
        if len(address.split(':')) != 2:
            yield False, "address should be in form 'hyph0://[host]:[port]' (':' not found)"
        host, port = address.split(':')
        if len(port) == 0 or any(not i.isdigit() for i in port):
            yield False, "address should be in form 'hyph0://[host]:[port]' (port is not numeric)"
        port = int(port)
        if len(host) == 0:
            yield False, "address should be in form 'hyph0://[host]:[port]' (host is empty)"
        self.client = SimpleChatClient(uname, host, port)
        yield None, "generating session keypair"
        self.client.set_keypair(ECC.generate(curve='p256'))
        yield None, "attempting to connect"
        asyncio.create_task(self.client.mainloop())
        wasstage = ""
        while True:
            await asyncio.sleep(0)
            if self.client._closed:
                stg = self.client._stage
                self.client = None
                yield False, f"client: {stg} failed"
            if wasstage == self.client._stage: continue
            wasstage = self.client._stage
            yield None, self.client._stage
            if self.client._stage == "running":
                break
        self._complete_client()
        yield True, "complete"

if __name__ == "__main__":
    app = Hyphen0ChatClientApp()
    app.run()