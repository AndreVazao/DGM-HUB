from fastapi import WebSocket
from threading import Lock
import asyncio


class LogStreamer:

    def __init__(self):

        self.clients=[]

        self.lock=Lock()

    async def connect(self,ws:WebSocket):

        await ws.accept()

        with self.lock:

            self.clients.append(ws)

    def disconnect(self,ws):

        with self.lock:

            if ws in self.clients:

                self.clients.remove(ws)

    async def broadcast(self,message:str):

        dead=[]

        for c in list(self.clients):

            try:

                await c.send_text(message)

            except:

                dead.append(c)

        for d in dead:

            self.disconnect(d)


STREAMER=LogStreamer()
