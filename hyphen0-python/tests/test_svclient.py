import asyncio

from hyphen0.server import Hyphen0Server
from hyphen0.client import Hyphen0Client

from Crypto.PublicKey import ECC

async def main():
    server = Hyphen0Server('', 1337)
    client = Hyphen0Client('localhost', 1337)

    server.set_keypair(ECC.generate(curve='p256'))
    client.set_keypair(ECC.generate(curve='p256'))

    asyncio.create_task(server.mainloop())
    await client.mainloop()

def run():
    print("--- test svclient ---")
    asyncio.run(main())