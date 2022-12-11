from .base import PyfronBackend
from flask import send_file, Flask, request 
from typing import Optional
import os 


class PyfronBasicBackend(PyfronBackend): 
    def start(self, *args, **kwargs): 
        app = Flask(__name__)
        app.add_url_rule("/", view_func=self.getRequest, methods=["GET"])
        app.add_url_rule('/<pageId>', view_func=self.getRequest, methods=["GET"])
        app.add_url_rule('/onEvent', view_func=self.postRequest, methods=["POST"])
        app.add_url_rule('/<pageId>/onEvent', view_func=self.postRequest, methods=["POST"])
        # files can only be stored in the 'static' folder in the main project route
        app.add_url_rule('/static/<filename>', view_func=self.sendFile)
        # this will block the thread and start listening for new requests
        app.run(
            host="0.0.0.0",
            port=8000,
            debug=bool(int(os.getenv("DEBUG", 1))), 
        )


    def getRequestData(self): 
        path: str = request.path
        if path.endswith("onEvent"): 
            path = "/" + path.split('/')[0]
        try: 
            json: dict = request.get_json(force=False) or {}
        except: 
            json = {}
        return (path, json)

    def sendFile(self, filename: str): 
        return send_file('../../static/' + filename)

    def getRequest(self, *args, **kwargs):
        return self.pyfron.onEvent(*self.getRequestData())

    def postRequest(self, *args, **kwargs): 
        return self.pyfron.onEvent(*self.getRequestData())



