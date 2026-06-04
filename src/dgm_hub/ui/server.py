from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from dgm_hub.ui.state import STATE
from dgm_hub.ui.log_stream import STREAMER


app=FastAPI()


class Incoming(BaseModel):

    action_id:str

    action_type:str

    description:str

    payload:dict


@app.post("/submit")

def submit(req:Incoming):

    STATE.add(req.model_dump())

    return {

        "ok":True

    }


@app.get("/pending")

def pending():

    return STATE.get_all()


@app.post("/approve/{action_id}")

def approve(action_id:str):

    item=STATE.remove(action_id)

    return {

        "approved":True,

        "action":item

    }


@app.post("/reject/{action_id}")

def reject(action_id:str):

    STATE.remove(action_id)

    return {

        "approved":False

    }


@app.websocket("/ws")

async def websocket_logs(ws:WebSocket):

    await STREAMER.connect(ws)

    try:

        while True:

            await ws.receive_text()

    except:

        STREAMER.disconnect(ws)


@app.get("/",response_class=HTMLResponse)

def ui():

    return """

<html>

<head>

<style>

body{

font-family:Arial;

display:flex;

height:100vh;

margin:0;

}

#left{

width:40%;

padding:20px;

overflow:auto;

border-right:1px solid #ccc;

}

#right{

width:60%;

padding:20px;

background:#111;

color:#0f0;

overflow:auto;

font-family:monospace;

}

.card{

border:1px solid #888;

padding:10px;

margin-bottom:10px;

}

.logline{

white-space:pre-wrap;

margin-bottom:4px;

}

button{

padding:8px;

margin-right:10px;

}

</style>

</head>

<body>

<div id='left'>

<h2>Approvals</h2>

<div id='actions'></div>

</div>

<div id='right'>

<h2>Runtime Logs</h2>

<div id='logs'></div>

</div>

<script>

async function refreshActions(){

let r=await fetch('/pending')

let data=await r.json()

let root=document.getElementById('actions')

root.innerHTML=''

data.forEach(x=>{

root.innerHTML+=`

<div class='card'>

<b>${x.action_type}</b>

<p>${x.description}</p>

<button onclick='approve("${x.action_id}")'>

Approve

</button>

<button onclick='reject("${x.action_id}")'>

Reject

</button>

</div>

`

})

}

async function approve(id){

await fetch('/approve/'+id,{method:'POST'})

refreshActions()

}

async function reject(id){

await fetch('/reject/'+id,{method:'POST'})

refreshActions()

}

const ws=new WebSocket(

"ws://127.0.0.1:8765/ws"

)

ws.onmessage=(ev)=>{

let logs=document.getElementById('logs')

logs.innerHTML+=

"<div class='logline'>"

+ev.data+

"</div>"

logs.scrollTop=logs.scrollHeight

}

setInterval(

refreshActions,

1000

)

refreshActions()

</script>

</body>

</html>

"""
