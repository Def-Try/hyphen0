# Hyphen0 Chat Application
A simple server-client chat application using the hyphen0 protocol with tkinter GUI.
Shows how base library can be used to secure connection in app and implement custom protocol packets.

## Features
- Secure communication using hyphen0 protocol with ECC encryption
- Real-time chat with message broadcasting
- User join/leave notifications
- Tkinter-based GUI with chat history
- Default TLSSteganoLayer hiding

## Requirements
- Python 3.7+
- pycryptodome
- hyphen0 library (from the parent project)

## Installation
1. Install pycryptodome:
   ```bash
   pip install pycryptodome
   ```

2. Ensure hyphen0 is available:
   ```bash
   # From the hyphen0 project root directory
   pip install -e hyphen0-python/
   ```

## Usage

### Starting the Server
```bash
python chat_server.py
```

The server will start on `localhost:1340`.

### Starting the Client
```bash
python chat_client.py
```

## GUI Features
- **Chat Display**: Shows all messages with timestamps and sender names
- **Message Input**: Type messages and press Enter or click Send

## Architecture

### Packets
Custom packets are defined in `chat_packets.py`:

class UserJoinClientbound(Packet):
    """Server notifies clients about new user"""
    _serverbound: bool = False
    username: pack.cstring

class UserLeaveClientbound(Packet):
    """Server notifies clients about user leaving"""
    _serverbound: bool = False
    username: pack.cstring

class UserListClientbound(Packet):
    """Server sends list of connected users to client"""
    _serverbound: bool = False
    users: pack.array(pack.cstring)

- `ChatRegisterServerbound(username: cstring)`: Sent by client on connection to tell information (now - username) about itself
- `ChatRegisterClientbound(username: cstring)`: Sent by server in response to `ChatRegisterServerbound` to confirm registration (possibly overriding information on conflicts)
- `UserListClientbound(users: array[cstring])`: Sent by server in response to `ChatRegisterServerbound` to tell about currently connected users
- `ChatMessageServerbound(message: cstring)`: Sent by client when it wants to send a message
- `ChatMessageClientbound(timestamp: uint64, sender: cstring, message: cstring)`: Broadcasted by server when message is sent by client.
- `UserJoinClientbound(username: cstring)`: Broadcasted by server (omitting the just-connected client) when new client is registered
- `UserLeaveClientbound(username: cstring)`: Broadcasted by server when client has disconnected

### Server (`chat_server.py`)
- Manages connected users
- Broadcasts messages to all clients
- Handles user join/leave notifications
- Maintains user list

### Client (`chat_client.py`)
- Tkinter-based GUI
- Connects to server and handles messages
- Updates UI in real-time
- Manages user list display