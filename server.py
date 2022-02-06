import socketio
import json
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
from db.offer import Offer, PydanticOffer, PydanticOffers
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

sio = socketio.AsyncServer(async_mode='sanic')

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

@sio.event
async def get_battles_list(sid, data):
    if clients[sid].state == ClientState.logging_in:
        sio.emit("verification_error", "You are not logged in")
        sio.disconnect(sid)

    db_sess = database.create_session()
    if data['user_id']:
        offers = db_sess.query(Offer).filter(Offer.user_id == data['user_id']).all()
    else:
        offers = db_sess.query(Offer).all()

    pydantic_offers = PydanticOffers.from_orm(offers)
    offers_json = pydantic_offers.json()


    sio.emit("battles_list", offers_json)
    sio.disconnect(sid)

@sio.event
async def create_battle_offer(sid, data):
    if clients[sid].state == ClientState.logging_in:
        sio.emit("verification_error", "You are not logged in")
        sio.disconnect(sid)

    db_sess = database.create_session()

    offer_db = Offer()

    offer_db.user_id = data['user_id']
    offer_db.nft_id = data['nft_id']

    db_sess.add(offer_db)
    db_sess.commit()

    json_offer = PydanticOffer.from_orm(offer_db)

    sio.emit("created_battle", json_offer)
    sio.disconnect(sid)



if __name__ == '__main__':
    app = Sanic(name='GameBack')
    sio.attach(app)
    app.run('0.0.0.0', 8080)
