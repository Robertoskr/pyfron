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
    
    async def getWebsocketMessage(self, websocket) -> dict: 
        message = await websocket.recv()
        return json.loads(message) 

    async def handler(self, websocket): 
        # first message that we receive is the user location (pageId) 
        # so we can send this socket to the correct page handler!
        await self.pyfron.handleWebsocketConnection(websocket) 

