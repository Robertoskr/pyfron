from copy import deepcopy
from .htmlelement import HTMLElement
from typing import Optional
from .exceptions import PageNotFound
from .backends import PyfronBackend
import json


class Pyfron:
    def __init__(self, pages: list[tuple[str, callable]], backend: PyfronBackend):
        self.pages = {p.path: p for p in pages}
        self.backend = backend(self)

    def start(self, *args, **kwargs): 
        self.backend.start(*args, **kwargs)

    def _finalize(self, page: HTMLElement):
        del page

    def _getPage(self, path: str) -> Optional[HTMLElement]:
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
        self.pages[page.path] = page

    def canHandleEvent(self, path: str, event: dict) -> bool: 
        try: 
            _ = self._getPage(path)
            return True
        except: 
            return False

    def onEvent(self, path: str, event: dict):
        """
        Handle a pyfron event, an event can be a get to one of our pages, or a user based event (click, submit) 
        any other event should be handled in the backend level.
        """
        page = self._getPage(path)
        if not page:
            return "", 400

        if not event: 
            # this is usually a get request, we don't need to process anything, just 
            # render the page and return it
            return self._renderPage(page=page)

        page.updateFromState(event.pop("state"))
        # fill up the elems id's
        page.updateElemId()

        # start processing the event, we have all set
        eventType: str = event.pop("eventType")
        # other events are not supported yet
        if eventType in ("submit", "click"):
            eventHandlerName = f"on{eventType}Request"
            if handler := getattr(page, eventHandlerName, None):
                page = handler(event) or page
                return self._renderPage(page=page, v2=True)
        return "WRONG_EVENT", 500
    
    def getWebsocketHandler(self, pageId: str): 
        page = self._getPage(pageId) 
        if not page: 
            return
        if not getattr(page, "onWebSocketConnection", None): 
            return 
        page.updateElemId()
        return page.onWebSocketConnection, (page, self,) 
    

    async def broadCastPageChanges(self, websocket, page): 
        content = self._renderPage(page=page, v2=True, final=False) 
        await websocket.send(json.dumps(content))  
    
