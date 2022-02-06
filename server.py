import socketio
import uvicorn
from typing import List, Union, Optional
from sqlalchemy.orm import Session
import web3
from web3 import Web3
from eth_account.messages import encode_defunct
from enum import Enum
from dataclasses import dataclass
from sanic import Sanic

# Randomness modules
import uuid
import random

# Database modules
from db import database
from db.session_keys import SessionKey
from db.round import Round
from db.move import Move, Choice
from db.accept import Accept
from db.offer import Offer
from db.battle import Battle

# Client states possible
class ClientState(Enum):
    logging_in = 1
    in_menu = 2
    in_battle = 3

# Client data class
@dataclass
class Client:
    session_key: str
    address: str = ''
    state: ClientState = ClientState.logging_in
    current_battle: int = -1

# Client connection data
clients = {}

sio = socketio.AsyncServer()

# Connect and disconnect handlers
@sio.event
async def connect(sid, environ, auth):
    print(f'Client {sid} connected')
    session_key = uuid.uuid4()
    clients[sid] = Client(session_key)
    sio.emit("session_key", {"session_key": session_key}, room=sid)

@sio.event
async def disconnect(sid):
    print(f'Client {sid} disconnected')
    del clients[sid]

# Signature auth event
@sio.event
async def verify_signature(sid, data):
    try:
        clients[sid].address = data['address']
        account_recovered = Web3.eth.account.recover_message(
            encode_defunct(text=clients[sid].session_key), signature=str(data['signature']))
    except Exception as ex:
        sio.emit("verification_error", str(ex))
        sio.disconnect(sid)

    if clients[sid].address == account_recovered:
        clients[sid].state = ClientState.in_menu
    else:
        sio.emit("verification_error", "Signature address recovered doesn't match the client address")
        sio.disconnect(sid)

if __name__ == '__main__':
    app = Sanic()
    sio.attach(app)
    app.run('0.0.0.0', 80)


