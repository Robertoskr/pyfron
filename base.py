from copy import deepcopy
from .htmlelement import HTMLElement
from typing import Optional
from .exceptions import PageNotFound
from .backends import PyfronBackend
import json


class Pyfron:
    """
    Main pyfron application, resposible for handling: 
    backend -> pages interactions: 
        the pyfron application abstracts all the page renderind/processing to the backend so the backend 
        only needs to adapt to the pyfron application 
    pages -> backend interactions: 
        when there are changes in the pages, that need to be comunicated to the client, (e.g websockets) 
        this class allows to communicate page with backend
    """
    def __init__(self, pages: list[tuple[str, callable]], backend: PyfronBackend):
        self.pages = {}
        for p in pages:
            self.addPage(p) 
        self.backend = backend(self)

    def start(self, *args, **kwargs): 
        """Start the backend service"""
        self.backend.start(*args, **kwargs)

    def _finalize(self, page: HTMLElement):
        """For not sharing the page state over multiple events, we need to delete the page object."""
        del page

    def _getPage(self, path: str) -> Optional[HTMLElement]:
        """
        Safely gets a fresh copy from the pages dict 
        """
        # normalize the path
        if not path.startswith("/"):
            path = "/" + path

        if not path in self.pages:
            return None
        return deepcopy(self.pages.get(path))

    def _renderPage(
        self, 
        path: Optional[str] = None, 
        page: Optional[HTMLElement] = None, 
        v2: bool = False, 
        final: bool = True, 
        **kwargs
    ) -> str:
        """
        Render the given or referenced page.
        """
        if not page:
            page = self._getPage(path)
        if not page:
            page = Div(class_name="not_found_page", text="not found")
        if v2: 
            res = page.renderV2(**kwargs) 
        else: 
            res = page.render(**kwargs)
        if final: 
            self._finalize(page)
        return res


    def addPage(self, page: HTMLElement):
        """
        Adds a page to the application
        """
        self.pages[page.path] = page

    def canHandleEvent(self, path: str, event: dict) -> bool: 
        """
        Returns true/false wheter Pyfron can handle the given event
        """
        try: 
            _ = self._getPage(path)
            return True
        except: 
            return False

    def onEvent(self, path: str, event: dict):
        """
        Handle a pyfron event, an event can be: get to one of our pages, a user based event (click, submit) 
        any other event should be handled in the backend level.
        """
        page = self._getPage(path)
        if not page:
            return "", 400

        if not event: 
            # this is usually a get request, we don't need to process anything, just 
            # render the page and return it
            return self._renderPage(page=page)

        page.prepare(remoteState=event.pop("state", {}))
        
        # start processing the event, we have all set
        eventType: str = event.pop("eventType")
        # other events are not supported yet
        if eventType in ("submit", "click"):
            eventHandlerName = f"on{eventType}Request"
            if handler := getattr(page, eventHandlerName, None):
                page = handler(event) or page
                return self._renderPage(page=page, v2=True)
        return "WRONG_EVENT", 500
    
    async def handleWebsocketConnection(self, websocket): 
        """
        Handles a websocket connection to our application
        """
        event: dict = await self.backend.getWebsocketMessage(websocket) 
        if event["type"] == "locationUpdate":
            pageId = event["pageId"]

            page = self._getPage(pageId) 
            # we create a copy of the page for each handler. 
            # is risky if we have a lot of clients, because it will consume quite a lot of memory, to have all this pages
            # in the ram at the same time. 
            # try to remove this (self._finalize) page when possible 
            page: Optional[HTMLElement] = self._getPage(pageId) 

            if page and hasattr(page, "onWebSocketConnection"): 
                page.prepare()
                # give the control to the user defined handler 
                await page.onWebSocketConnection(websocket, page, self) 
                self._finalize(page) 

    async def broadCastPageChanges(self, websocket, page): 
        """
        Method used to broadcast the changes of a page to a the client, via the given websocket 
        """
        content = self._renderPage(page=page, v2=True, final=False) 
        await websocket.send(json.dumps(content))  
    
