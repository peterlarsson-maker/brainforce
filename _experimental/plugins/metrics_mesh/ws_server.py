import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI(title="Brainforce Metrics Mesh")
CLIENTS = set()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    CLIENTS.add(ws)
    try:
        await ws.send_text("hello:metrics-mesh")
        while True:
            msg = await ws.receive_text()
            # simple echo + client count
            await ws.send_text(f"echo:{msg}|clients={len(CLIENTS)}")
    except WebSocketDisconnect:
        pass
    finally:
        CLIENTS.discard(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8110)