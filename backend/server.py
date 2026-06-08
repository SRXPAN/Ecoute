from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from typing import List


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


app = FastAPI(title="AI Interview Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Interview Assistant Backend",
        "active_connections": len(manager.active_connections)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        await manager.send_json(websocket, {
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established"
        })

        while True:
            data = await websocket.receive_json()

            command = data.get("command")

            if command == "ping":
                await manager.send_json(websocket, {
                    "type": "response",
                    "command": "ping",
                    "message": "pong"
                })
            else:
                await manager.send_json(websocket, {
                    "type": "response",
                    "command": command,
                    "message": f"Received command: {command}",
                    "data": data
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await manager.send_json(websocket, {
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
