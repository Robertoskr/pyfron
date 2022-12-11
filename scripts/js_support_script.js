//base function to postData to the server 
async function postData(url = '', data = {}) {
    // Default options are marked with *
    const response = await fetch(url, {
        method: 'POST', // *GET, POST, PUT, DELETE, etc.
        mode: 'cors', // no-cors, *cors, same-origin
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: {
          'Content-Type': 'application/json'
          // 'Content-Type': 'application/x-www-form-urlencoded',
        },
        redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
        body: JSON.stringify(data) // body data type must match "Content-Type" header
    }) ;
    return response.text(); // parses JSON response into native JavaScript objects
} 
    

function getCurrentURL () {
    return window.location.href
}

function htmlToElement(html) { 
    var template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content;
} 

function updatePageFromChanges(changes) { 
    for(const [key, value] of Object.entries(changes)) {
        element = document.getElementsByClassName(key)[0]
        content = htmlToElement(value) 
        if (key == "pyfron_body") { 
            element.replaceChildren(...content.children) 
        } else {
            element.parentNode.replaceChild(content.firstElementChild, element) 
        } 
    } 
} 

//handler for the user clicks
function onClickListener(elemId) { 
    toSend = {state: page_props, eventType: 'click', target: elemId};
    postData(getCurrentURL() + "/onEvent", toSend).then(response => { 
        let body = document.getElementsByTagName("body")[0];
        let asJson = JSON.parse(response) 
        updatePageFromChanges(asJson.changes) 
        let state = asJson.state;
        page_props = state;
    })
}

// Function to handle when the user submits a form (for example) 
function onSubmitListener(event) { 
    parent = event.srcElement;
    toSend = {state: page_props, eventType: 'submit', target: parent.attributes.elemId.nodeValue};
    stack = [parent];
    while(stack.length > 0) { 
        let actual = stack.pop();
        for(let i = 0; i < actual.children.length; i++ ) { 
            let child = actual.children[i]; 
            if(child.attributes.key) { 
                toSend[child.attributes.key.nodeValue] = child.value;
            }
            stack.push(child);
        }
    }

    //send this to the frontend backend 
    postData(getCurrentURL() + "/onEvent", toSend).then(response => { 
        let body = document.getElementsByTagName("body")[0];
        let asJson = JSON.parse(response) 
        updatePageFromChanges(asJson.changes) 
        let state = asJson.state;
        page_props = state;
    })
    event.preventDefault();
} 

function receiveWebsocketMessages(websocket) { 
    websocket.addEventListener("message", ({data}) => {
        const parsed = JSON.parse(data) 
        page_props = parsed.state;
        updatePageFromChanges(parsed.changes);  
    })
} 

function notifyWebsocketLocation(websocket) { 
    const url = new URL(getCurrentURL()) 
    const location = {"type": "locationUpdate", "pageId": url.pathname}
    websocket.send(JSON.stringify(location));
} 

function waitForSocketConnection(websocket, callback) { 
    if (websocket.readyState === 1) { 
        callback();
    }else { 
        setTimeout( function () { 
            waitForSocketConnection(websocket, callback);
        }, 1);
    } 
} 
function main() { 
    let b = document.getElementsByTagName("body")[0];
    b.addEventListener('submit', onSubmitListener);

    //try to add websocket support! 
    const websocket = new WebSocket("ws://localhost:8001/");
    waitForSocketConnection(websocket, () => { 
        notifyWebsocketLocation(websocket); 
        receiveWebsocketMessages(websocket); 
    });
} 

main()

