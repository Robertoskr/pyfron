
def loadScript(filename: str) -> str: 
    with open(filename, "r") as f: 
        return "<script>" + f.read() + "</script>" 
JS_SUPPORT_SCRIPT = loadScript("pyfron/scripts/js_support_script.js") 
