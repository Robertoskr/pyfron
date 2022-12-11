from pyfron.backends import PyfronBackend 
import asyncio
import websockets 
import os 
import json 
from urllib.parse import unquote, urlparse

class WebSocketBackend(PyfronBackend): 
    def start(self) : 
        asyncio.run(self.startWebSocketServer()) 

    async def startWebSocketServer(self): 
        port: int = os.getenv("WEBSOCKET_SERVER_PORT", 8001)
        async with websockets.serve(self.handler, "", port): 
            print(f"started websocket server at: {port}") 
            await asyncio.Future()


    async def handler(self, websocket): 
        # each handler corresponds to one user 
        while True: 
            # first message that we receive is the user location (pageId) 
            # so we can send this socket to the correct page handler!
            message = await websocket.recv()
            event = json.loads(message)
            if event["type"] == "locationUpdate":
                pageId = event["pageId"]
                # handler should be an async function that accepts the websocket !
                handler, args = self.pyfron.getWebsocketHandler(pageId) 
                await handler(websocket, *args) 
                break

