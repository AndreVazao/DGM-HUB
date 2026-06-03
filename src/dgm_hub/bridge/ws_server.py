from fastapi import WebSocket
import json

clients = []

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        clients.remove(websocket)

async def broadcast(message: dict):
    for client in clients:
        await client.send_json(message)
