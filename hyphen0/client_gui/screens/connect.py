from textual.app import App

from textual.screen import ModalScreen

from textual.widgets import Header, Footer, \
                            Input, Button, Label
from textual.containers import Center, Middle, Vertical
from textual import on

import asyncio
import random

class ConnectScreen(ModalScreen):
    def __init__(self, app: App, *args, **kwargs):
        self._app = app
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical():
            with Middle():
                yield Input(f"user_{random.randint(100,999)}", placeholder="Username", id="connect-username")
                yield Input("hyph0://localhost:12345", placeholder="Hyphen0 chat address", id="connect-address")
                with Center():
                    yield Button("Connect", id="connect-connect")
                    yield Label("status...", id="connect-status")

    @on(Input.Submitted, "#connect-address")
    def _(self, event):
        self.query_one("#connect-address").focus()
    @on(Input.Submitted, "#connect-address")
    # @on(Button.Clicked, "#connect-connect")
    async def try_connecting(self, event: Input.Submitted):
        self.query_one("#connect-username").disabled = True
        self.query_one("#connect-address").disabled = True
        self.query_one("#connect-connect").disabled = True
        statuslabel = self.query_one("#connect-status")
        async for (ok, message) in self.app.attempt_connecting(self.query_one("#connect-username").value, event.value):
            await asyncio.sleep(0)
            self.app.add_message("SYSTEM", f"connect: {message}")
            statuslabel.content = message
            if ok != None: break
        if not ok:
            self.query_one("#connect-username").disabled = False
            self.query_one("#connect-address").disabled = False
            self.query_one("#connect-connect").disabled = False
            return
        self.dismiss(True)
