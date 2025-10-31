import asyncio, websockets

async def main():
    uri = "ws://localhost:8110/ws"
    async with websockets.connect(uri) as ws:
        hello = await ws.recv()
        print(hello)
        await ws.send("ping")
        resp = await ws.recv()
        print(resp)

if __name__ == "__main__":
    asyncio.run(main())