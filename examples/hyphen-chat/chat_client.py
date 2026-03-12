#!/usr/bin/env python3
"""
Chat Client using hyphen0 library with asynctkinter for GUI
"""

import asyncio
import tkinter as tk
from tkinter import scrolledtext as tkscrolledtext
import datetime
import random
import time
from hyphen0.client import Hyphen0Client
from hyphen0.stegano import TLSSteganoLayer
from chat_packets import ChatRegisterServerbound, ChatRegisterClientbound, ChatMessageServerbound, ChatMessageClientbound, UserJoinClientbound, UserLeaveClientbound, UserListClientbound

from Crypto.PublicKey import ECC

class Hyphen0ChatClient(Hyphen0Client):
    _trace_hooks: bool = False
    _username: str
    _tkroot: tk.Tk
    def __init__(self, host: str, port: int, username: str, tkroot: tk.Tk):
        super().__init__(host, port, TLSSteganoLayer())
        self._username = username
        self._tkroot = tkroot
    
    async def _event_client_handshake(self):
        self._add_message(int(time.time() * 1000), 'Log', "Handshake")
    async def _event_crypt_modeselected(self, mode):
        self._add_message(int(time.time() * 1000), 'Log', f"Encryption mode selected: {mode}")
    async def _event_crypt_kexok(self):
        self._add_message(int(time.time() * 1000), 'Log', f"Key Exchange complete")
    async def _event_crypt_starting(self):
        self._add_message(int(time.time() * 1000), 'Log', f"Encryption starting")
    async def _event_crypt_complete(self):
        self._add_message(int(time.time() * 1000), 'Log', f"Encryption complete and verified")

    async def _event_client_connected(self):
        self._add_message(int(time.time() * 1000), 'Log', "Connected!")
        self._socket.write_packet(ChatRegisterServerbound(username=self._username.encode()))
    def _event_ptype_ChatMessageClientbound_received(self, packet: ChatMessageClientbound):
        if packet.sender.decode() == client._username:
            return
        self._add_message(packet.timestamp, packet.sender.decode(), packet.message.decode())
    def _event_ptype_ChatRegisterClientbound_received(self, packet: ChatRegisterClientbound):
        self._add_message(int(time.time() * 1000), 'Log', "Registered!")
        self._username = packet.username.decode()
        self._add_message(int(time.time() * 1000), 'Log', f"Logged in as {self._username}")
    def _event_ptype_UserListClientbound_received(self, packet: UserListClientbound):
        self._add_message(int(time.time() * 1000), 'Userlist', f"Connected users:")
        for username in packet.users:
            self._add_message(int(time.time() * 1000), 'Userlist', f"  {username.decode()}")
    def _event_ptype_UserJoinClientbound_received(self, packet: UserJoinClientbound):
        self._add_message(int(time.time() * 1000), 'Userlist', f"+ {packet.username.decode()} joined")
    def _event_ptype_UserLeaveClientbound_received(self, packet: UserLeaveClientbound):
        self._add_message(int(time.time() * 1000), 'Userlist', f"- {packet.username.decode()} left")

    def _add_message(self, timestamp, sender, message):
        self._tkroot.txt.config(state=tk.NORMAL)
        self._tkroot.txt.insert(tk.END, f"[{datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%B %d, %Y @ %I:%M %p')}][{sender}] {message}\n")
        self._tkroot.txt.config(state=tk.DISABLED)
        self._tkroot.txt.see(tk.END)
    def _send_message(self, message):
        if message == '': return
        self._add_message(int(time.time() * 1000), self._username, message)
        self._socket.write_packet(ChatMessageServerbound(message=message.encode()))

root = tk.Tk()
root.title("Hyphen0 Example Chat Client")
root.geometry("800x600")

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

root.txt = tkscrolledtext.ScrolledText(root, wrap=tk.WORD)
root.txt.config(state=tk.DISABLED)
root.txt.config(cursor="arrow")
root.txt.grid(row=0, column=0, columnspan=4, sticky='nesw')

root.message_entry = tk.Entry(root)
root.message_entry.grid(row=1, column=0, columnspan=3, sticky='nesw')
root.send_button = tk.Button(root, text="Send")
root.send_button.grid(row=1, column=3, sticky='nesw')

client = Hyphen0ChatClient('localhost', 1340, f'testuser_{random.randint(10000, 99999)}', root)
client.set_keypair(ECC.generate(curve='P-256'))

root.send_button.config(command=lambda: client._send_message(root.message_entry.get()) or root.message_entry.delete(0, tk.END))
root.message_entry.bind('<Return>', lambda e: client._send_message(root.message_entry.get()) or root.message_entry.delete(0, tk.END))

root.done = False
root.protocol("WM_DELETE_WINDOW", lambda: setattr(root, 'done', True))

async def main():
    client_task = asyncio.create_task(client.mainloop())

    while not root.done:
        root.update()
        await asyncio.sleep(0)

        if client_task.done():
            raise client_task.exception()
    await client.close()
    client_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())