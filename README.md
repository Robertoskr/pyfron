# pyfron
Python ssr frontend framework with bateries included.


`from pyfron.htmlelement import HTMLElement, Page, H1, P, Div
from pyfron.base import Pyfron
import asyncio

async def handleWebsocketConnection(websocket, document: HTMLElement, application: Pyfron): 
    while True: 
        await asyncio.sleep(.5) 
        main_div = document.findElementsByClassName("main_div")[0]
        n = len(main_div.childrens) 
        document.addElement("main_div", 
                            P(class_name="some_element_{n}", text="Hola") ) 
        await application.broadCastPageChanges(websocket, document) 



webSocketTestPage = Page(
    path="/websocket-test", 
    description="Test websockets in pyfron framework!", 
    onWebSocketConnection=handleWebsocketConnection, 
    childrens=[
        Div(
            class_name="main_div", 
            childrens=[
                P(
                    class_name="text_something", 
                    text="Some random text", 
                    style="font-size:1rem; color:blue;"
                )
            ]
        ) 
    ]
) `
