"""
Simple chat server using hyphen0 protocol.
"""
import asyncio
import time
from Crypto.PublicKey import ECC

from hyphen0.server import Hyphen0Server
from hyphen0.stegano import TLSSteganoLayer
from hyphen0.packets.packet import Kick, Disconnect
from chat_packets import ChatRegisterServerbound, ChatRegisterClientbound, ChatMessageServerbound, ChatMessageClientbound, UserJoinClientbound, UserLeaveClientbound, UserListClientbound


class ChatServer(Hyphen0Server):
    _trace_hooks: bool = False
    def __init__(self, host: str, port: int):
        super().__init__(host, port, TLSSteganoLayer())
        self.connected_users = {}  # username -> client socket
        self.user_sockets = {}  # socket -> username
        
    async def _event_client_connected(self, client):
        print(f"[CHAT] Client connected: {client.getnicename()}")
        
    async def _event_packet_received(self, client, packet):
        """Handle incoming packets"""
        if isinstance(packet, ChatMessageServerbound):
            await self._handle_chat_message(client, packet)
        elif isinstance(packet, Disconnect):
            await self._handle_disconnect(client, packet)
            
    async def _handle_chat_message(self, client, packet):
        """Broadcast chat message to all connected clients"""
        if client not in self.user_sockets:
            return  # User not registered yet
            
        username = self.user_sockets[client]
        message = packet.message.decode('utf-8')
        
        print(f"[CHAT] {username}: {message}")
        
        # Broadcast message to all connected clients
        chat_packet = ChatMessageClientbound(
            message=message.encode('utf-8'),
            sender=username.encode('utf-8'),
            timestamp=int(time.time() * 1000)
        )
        
        for sock in self.connected_users.values():
            sock.write_packet(chat_packet)
            
    async def _handle_disconnect(self, client, packet):
        """Handle client disconnection"""
        if client in self.user_sockets:
            username = self.user_sockets[client]
            await self._remove_user(client, username)
            
    async def _event_client_disconnecting(self, client):
        """Called when a client is disconnecting"""
        if client in self.user_sockets:
            username = self.user_sockets[client]
            await self._remove_user(client, username)
            
    async def _remove_user(self, client, username):
        """Remove user from chat and notify others"""
        if username in self.connected_users:
            del self.connected_users[username]
        if client in self.user_sockets:
            del self.user_sockets[client]
            
        print(f"[CHAT] User left: {username}")
        
        # Notify all clients about user leaving
        leave_packet = UserLeaveClientbound(username=username.encode('utf-8'))
        for sock in self.connected_users.values():
            sock.write_packet(leave_packet)
            
    async def work(self, client):
        """Main work loop for connected client"""
        # Wait for user to register with a username
        username = await self._register_user(client)
        if not username:
            return
            
        # Send welcome message and user list
        welcome_packet = ChatMessageClientbound(
            message=f"Welcome to the chat, {username}!".encode('utf-8'),
            sender="Server".encode('utf-8'),
            timestamp=int(time.time() * 1000)
        )
        client.write_packet(welcome_packet)
        
        # Notify all clients about new user
        join_packet = UserJoinClientbound(username=username.encode('utf-8'))
        for sock in self.connected_users.values():
            if sock == client: continue # no need to notify client that just connected anyways
            sock.write_packet(join_packet)
        
        # Continue with normal packet handling
        await super().work(client)
        
    async def _register_user(self, client):
        register_packet = await client.wait_for_packet(ChatRegisterServerbound)
        username = register_packet.username.decode()
        
        if username in self.connected_users or username == 'Server':
            # Username conflict, try to find a unique one
            counter = 1
            while f"{username}_{counter}" in self.connected_users:
                counter += 1
            username = f"{username}_{counter}"
            
        self.connected_users[username] = client
        self.user_sockets[client] = username

        client.write_packet(ChatRegisterClientbound(username=username.encode()))
        
        print(f"[CHAT] User registered: {username}")

        user_list = [i.encode() for i in self.connected_users.keys()]
        user_list_packet = UserListClientbound(users=user_list)
        client.write_packet(user_list_packet)

        return username


def main():
    """Start the chat server"""
    # Generate server keypair
    keypair = ECC.generate(curve='P-256')
    
    # Create and start server
    server = ChatServer('localhost', 1340)
    server.set_keypair(keypair)
    
    print("Starting chat server on localhost:1340")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")


if __name__ == "__main__":
    main()