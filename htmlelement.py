import copy
from typing import Optional, Union

from pyfron.constants import JS_SUPPORT_SCRIPT
from pyfron.exceptions import ElementNotFound
from importlib import import_module
from collections import deque


class HTMLElement(object):
    # base attributes
    def __init__(self, **kwargs):
        """
        init function for dinamically support al type of allocations that may be needed in other steps
        """
        for k, v in kwargs.items():
            if v == "__NTA__":
                continue
            elif isinstance(v, str) and v.startswith("__BUILT_IN__"):
                v = self.getBuiltInValue(v.split("-")[1])
            self.__setattr__(k, v)

        kwargs["class"] = kwargs.get("class_name", "")
        self.moveValuesToAttrs(kwargs, ["class"])

        if not getattr(self, "attributes", None):
            self.attributes = {}
        if not getattr(self, "tag", None):
            self.tag = "div"
        if not getattr(self, "text", None):
            self.text = ""
        if not getattr(self, "style", None):
            self.style = ""
        if not getattr(self, "childrens", None):
            self.childrens = []
        if not getattr(self, "elemId", None):
            self.elemId = ""
        if not getattr(self, "class_name", None):
            self.class_name = ""

        self._changed: bool = False

    def __setattr__(self, key, value): 
        # we need to detect that an element has changed, so we can efficiently update the client page 
        # without updating and renderind all the page 
        super().__setattr__(key, value) 
        if key != "_changed": 
            super().__setattr__("_changed", True)

    @staticmethod
    def getBuiltInValue(path: str) -> any:
        """Get a built in value, given the path,
        path should be: {module_path}__{value that we want}
        """
        moduleName, builtInName = path.split("__")
        module = import_module(moduleName)
        return getattr(module, builtInName)

    def updateElemId(self, newId: str = ""):
        """
        Update the elemId of this item and its childrens
        """
        if not newId:
            newId = "0"
        self.elemId = newId
        # we set to false, because is changed to True when we update the elemId's 
        self._changed = False

        self.attributes["elemId"] = self.elemId
        for i, child in enumerate(self.childrens):
            child.updateElemId(f"{self.elemId}-{i}")

    def getAttributesString(self) -> str:
        result = ""
        for k, v in self.attributes.items():
            result += f"{k}={v} "
        return result

    def dumpToDict(self) -> dict:
        res = {}
        _obj = copy.copy(self.__dict__)
        childrens = _obj.pop("childrens", [])
        # used to rebuild the obj from a dict
        res["class_ref"] = f"{__name__}__{self.__class__.__name__}"

        def cleanValues(value) -> any:
            if isinstance(value, bool): 
                # TODO, we should support this!
                return None
            elif isinstance(value, (str, int, float)):
                return value
            

            elif isinstance(value, dict):
                for k, v in value.items():
                    if newVal := cleanValues(v):
                        value[k] = newVal
                    else:
                        value.pop(k)
                return value

            elif isinstance(value, list):
                newList = []
                for v in value:
                    if newVal := cleanValues(v):
                        newList = v
                return newList
            return None

        for k, v in _obj.items():
            clean = cleanValues(v)
            if clean is not None:
                res[k] = clean
            elif callable(v):
                res[k] = f"__BUILT_IN__-{v.__module__}__{v.__name__}"
            else:
                # this element is not js translatable, so we must have it in the code
                # the build_in string is reserved to the pyfron framework
                # __NTA keyword is filtered in the init function
                res[k] = f"__NTA__"

        # add the childrens last.
        res["childrens"] = [ch.dumpToDict() for ch in childrens]

        return res

    @staticmethod
    def fromDict(rawElem: dict) -> "HTMLElement":
        childrens: list = rawElem.pop("childrens", [])
        parentClass: type = HTMLElement.getBuiltInValue(rawElem["class_ref"])
        parent: HTMLElement = parentClass(**rawElem)
        parent.childrens = [HTMLElement.fromDict(ch) for ch in childrens]
        return parent
    
    def prepare(self, remoteState: Optional[dict] = None): 
        """
        Prepare the page object before handling an event.
        """
        if remoteState: 
            self.updateFromState(remoteState) 
        self.updateElemId()

    def updateFromState(self, state: dict):
        """
        Update the current page object with the state that is currently online.
        """
        childrens = state.pop("childrens", [])
        finalChildrens: list[HTMLElement] = [
            HTMLElement.fromDict(ch) for ch in childrens
        ]
        # OLD way, deprecated
        # for oC in childrens:
        #    if oC["class_name"] and (
        #        local := localChildrensMapping.get(oC["class_name"])
        #    ):
        #        local.updateFromState(oC)
        #    else:
        #        # not in the previously defined childrens, we need to guess some values on the fly,
        #        # and have posibly corrupted data 0(
        #        local = self.fromDict(oC)
        #    finalChildrens.append(local)

        self.childrens = finalChildrens
        self.__init__(**state)

    def renderStyle(self) -> str:
        if not self.style or not self.class_name:
            result = ""
        else:
            result = f".{self.class_name}" + "{" + self.style + "}"
        # add the hover to the element
        if getattr(self, "hover", None):
            result += f".{self.class_name}:hover" + "{" + self.hover + "}"

        for ch in self.childrens:
            result += ch.renderStyle()
        return result

    def addOnClickListener(self):
        if getattr(self, "onClick", None):
            k = {"onclick": f"onClickListener('{self.elemId}')"}
            self.moveValuesToAttrs(k, ["onclick"])

    def renderV2(self, *args, **kwargs) -> Union[dict, str]: 
        """
        New way of rendering an object, only used on events like: click, submit, 
        is faster than v1 way, because we only render the elements that have changes, so we only update those in the base page 
        BEWARE, when this method is called we already asumme that the client page has the JS support files, etc, so we don't 
        send them again here 
        """
        # a mapping of class str : rendered object HTML string 
        changes: dict[str, str] = {}

        elems = deque([self])
        level = 0
        while elems: 
            l = len(elems) 
            for _ in range(l): 
                elem = elems.pop()
                if elem._changed: 
                    # we send level = 1000 so we don't treat this as a upper level item 
                    changes[elem.class_name] = elem.render(level=-1, *args, **kwargs)
                else: 
                    for el in elem.childrens: 
                        elems.appendleft(el)
            level += 1

        return {"state": self.dumpToDict(), "changes": changes}

    def getStyle(self, level: int = 0) -> str: 
        """
        return the style of an element, formated to fit into the properties of an 
        html element 
        """
        return f"style='{self.style}'"
    
    def getJSSupportScripts(self): 
        script = f"<script>let page_props = {self.dumpToDict()}; </script>"
        # only add the js support script one time
        script += JS_SUPPORT_SCRIPT
        return script 

    # can be overriden in the childrens
    def render(self, level: int = 0, dictFormat: bool = False) -> str:
        # update the elemId and the children elems
        if not self.elemId:
            self.updateElemId()

        # add the onClickListener to the object if needed
        self.addOnClickListener()

        # base render method that can be overrided in childrens
        # NOT recommended to change this method in the childrens
        attributes: str = self.getAttributesString()

        # build the html tag entry, and fill with the childrens renders
        style = '' 
        if level == -1: 
            style = self.getStyle() 

        content = f"<{self.tag} {attributes} {style}>{self.text}"
        for children in self.childrens:
            # TODO we can do this without recursion
            # if level == -1 we want to keep it as it is 
            content += children.render(
                    level=level if level ==  -1 
                    else (level + 1) 
            )

        # close the html thingy
        content += f"</{self.tag}>"

        if level == 0:
            # add the js support things for this page! 
            content += self.getJSSupportScripts()
            # add the css to this page!
            content += f"<style>{self.renderStyle()}</style>"

        return content

    def findChildrenByElemId(self, elemId: str):
        childrenList = list(reversed(elemId.split("-")))
        # we need to pop the first one (this children id)
        childrenList.pop()
        parent = self
        while parent.elemId != elemId:
            parent = parent.childrens[int(childrenList[-1])]
            childrenList.pop()
        return parent

    def findElementsByClassName(self, className: str) -> list["HTMLElement"]:
        """
        Finds an element in the document based on the className,
        it scans the document with a breath first search algorithm, and returns the document
        if found inside, else None,
        runtime: O(N) where N is the length of HTMLElements in the document
        """
        visited: set[str] = set()
        notVisited: list[HTMLElement] = [self]
        elemsFound: list[HTMLElement] = []
        while notVisited:
            actual = notVisited.pop()
            if actual.elemId in visited:
                continue
            visited.add(actual.elemId)

            if actual.class_name == className:
                elemsFound.append(actual)

            for ch in actual.childrens:
                notVisited.append(ch)

        return elemsFound

    def getParentElemId(self) -> str:
        if self.elemId == "0":
            return ""
        idx = len(self.elemId) - 1
        while self.elemId[idx] != "-":
            idx -= 1

        return self.elemId[:idx]

    def removeElement(self, element: "HTMLElement", _raise=True):
        """
        Removes and element from the document, if found,
        if it is not found, a ElementNotFound exception will be raised. ( if _raise is True )
        """

        try:
            # get the parent Id of the element
            parentElemId = element.getParentElemId()
            if not parentElemId:
                raise ElementNotFound(
                    f"element with id: {element.elemId} has no parent"
                )
            parentElement = self.findChildrenByElemId(parentElemId)
            parentElement._changed = True
            parentElement.childrens.remove(element)
        except (ElementNotFound, ValueError, IndexError) as e:
            if not _raise:
                pass
            raise e

    def removeElements(self, elements: list["HTMLElement"], *args, **kwargs):
        for elem in elements:
            self.removeElement(elem, *args, **kwargs)

    def remove(self, document: "HTMLElement", *args, **kwargs):
        """Remove the current element from the page,
        if the element could not exists in the project, you should pass the _raise=False flag"""
        if self.elemId != "":
            self.removeElement(self, *args, **kwargs)
        else:
            document.removeElements(
                document.findElementsByClassName(self.class_name), *args, **kwargs
            )

    def addElement(self, parent: Union[str, "HTMLElement"], element: "HTMLElement", index: Optional[int] = None):
        if isinstance(parent, str):
            parentElement = self.findElementsByClassName(parent)[0]
        else: 
            parentElement = parent
        parentElement._changed = True
        if index is not None: 
            parentElement.childrens.insert(index, element)
        else: 
            parentElement.childrens.append(element)
    

    def onsubmitRequest(self, event: dict):
        # we need to find the target element
        targetId = event["target"]
        targetElement: Optional[HTMLElement] = self.findChildrenByElemId(targetId)
        return targetElement.onSubmit(event, self)

    def onclickRequest(self, event: dict):
        targetId = event["target"]
        targetElement: Optional[HTMLElement] = self.findChildrenByElemId(targetId)
        return targetElement.onClick(self)

    def moveValuesToAttrs(self, kwargs: dict, keys: list[str]):
        if not getattr(self, "attributes", None):
            self.attributes = {}
        for k in keys:
            if kwargs.get(k):
                self.attributes[k] = kwargs.pop(k)


class Page(HTMLElement):
    def __init__(self, **kwargs):
        self.tag = "body"
        kwargs.pop("class_name", "")
        # page element should always have a path :)
        self.path = kwargs.pop("path")
        super(Page, self).__init__(
            style=kwargs.pop("style", ""),
            **kwargs,
            class_name="pyfron_body",
        )

    def render(self, *args, **kwargs):
        result = super(Page, self).render(*args, **kwargs)
        if kwargs.get("dictFormat", False):
            result["page"] += f"<style>{self.style}</style>"
        else:
            result += f"<style>{self.style}</style>"
        return result


class Form(HTMLElement):
    def __init__(self, **kwargs):
        kwargs["tag"] = "form"
        super(Form, self).__init__(**kwargs)


class H1(HTMLElement):
    def __init__(self, **kwargs):
        kwargs["tag"] = "h1"
        super(H1, self).__init__(**kwargs)


class P(HTMLElement):
    def __init__(self, **kwargs):
        kwargs["tag"] = "p"
        super(P, self).__init__(**kwargs)


class Input(HTMLElement):
    def __init__(self, **kwargs):
        # this class is the parent of others 
        if not "tag" in kwargs: 
            kwargs["tag"] = "input"
        self.moveValuesToAttrs(kwargs, ["type", "value", "key"])
        super(Input, self).__init__(**kwargs)


class TextArea(Input): 
    def __init__(self, **kwargs): 
        kwargs["tag"] = "textarea"
        kwargs["type"] = ""
        self.moveValuesToAttrs(kwargs, ["cols", "rows"])
        super(TextArea, self).__init__(**kwargs)


class Image(HTMLElement):
    def __init__(self, **kwargs):
        kwargs["tag"] = "img"
        self.moveValuesToAttrs(kwargs, ["src", "alt"])
        super(Image, self).__init__(**kwargs)


class Button(HTMLElement):
    def __init__(self, **kwargs):
        kwargs["tag"] = "button"
        # this handler is in the js support file
        super(Button, self).__init__(**kwargs)


class Link(HTMLElement):
    def __init__(self, **kwargs):
        kwargs["tag"] = "a"
        self.moveValuesToAttrs(kwargs, ["href"])
        super(Link, self).__init__(**kwargs)


class Div(HTMLElement):
    ...


class Select(HTMLElement):
    def __init__(self, **kwargs):
        kwargs["tag"] = "select"
        kwargs["childrens"] = kwargs.pop("childrens", [])
        self.moveValuesToAttrs(kwargs, ["key", "value"])
        super(Select, self).__init__(**kwargs)


class Option(HTMLElement):
    def __init__(self, **kwargs):
        kwargs["tag"] = "option"
        self.moveValuesToAttrs(kwargs, ["value"])
        super(Option, self).__init__(**kwargs)


class RawHTMLElement(HTMLElement):
    # TODO support parsing from HTML to HTMLElement, and do that in the init based on the filename
    def render(self, *args, **kwargs):
        content = open(self.filename, "r")
        return content.read()

class WebSocket(HTMLElement): 
    # TODO: implement this
    pass

