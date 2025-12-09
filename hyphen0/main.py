import asyncio

from protocol.server import Hyphen0Server
from protocol.client import Hyphen0Client

async def main():
    server = Hyphen0Server('', 12345)
    client = Hyphen0Client('127.0.0.1', 12345)

    # client.start()
    # server.serve()

    asyncio.create_task(server.mainloop())
    await asyncio.sleep(1)
    await client.mainloop()


if __name__ == "__main__":
    asyncio.run(main())
