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
from db.accept import Accept, PydanticAccept, PydanticAccepts
from db.offer import Offer, PydanticOffer, PydanticOffers
from db.battle import Battle, PydanticBattle

# For checking if correct data passed to function


def check_passed_data(dic: dict, *names):
    for name in names:
        if name not in dic:
            return False
    return True


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
            encode_defunct(text=clients[sid].session_key),
            signature=str(data['signature']))
    except Exception as ex:
        sio.emit("verification_error", str(ex))
        sio.disconnect(sid)

    if clients[sid].address == account_recovered:
        clients[sid].state = ClientState.in_menu
    else:
        sio.emit(
            "verification_error",
            "Signature address recovered doesn't match the client address")
        sio.disconnect(sid)


@sio.event
async def get_battles_list(sid, data):
    if clients[sid].state == ClientState.logging_in:
        sio.emit("verification_error", "You are not logged in")
        sio.disconnect(sid)

    db_sess = database.create_session()
    if data['user_id']:
        offers = db_sess.query(Offer).filter(
            Offer.user_id == data['user_id']).all()
    else:
        offers = db_sess.query(Offer).all()

    pydantic_offers = PydanticOffers.from_orm(offers)
    dict_offers = pydantic_offers.dict()

    sio.emit("battles_list", json.dumps(dict_offers))
    sio.disconnect(sid)


@sio.event
async def create_battle_offer(sid, data):
    if clients[sid].state == ClientState.logging_in:
        sio.emit("verification_error", "You are not logged in")
        sio.disconnect(sid)

    if not check_passed_data(data, 'user_id', 'nft_id'):
        sio.emit("wrong_input", "You need to pass 'user_id' and 'nft_id'")
        sio.disconnect(sid)

    db_sess = database.create_session()

    offer_db = Offer()

    offer_db.user_id = data['user_id']
    offer_db.nft_id = data['nft_id']

    db_sess.add(offer_db)
    db_sess.commit()

    pydantic_offer = PydanticOffer.from_orm(offer_db)
    dict_offer = pydantic_offer.dict()

    sio.emit("created_battle", json.dumps(dict_offer))
    sio.disconnect(sid)


@sio.event
async def get_recommended_battles(sid):
    if clients[sid].state == ClientState.logging_in:
        sio.emit("verification_error", "You are not logged in")
        sio.disconnect(sid)

    db_sess = database.create_session()

    all_offers = db_sess.query(Offer).all()
    if len(all_offers) >= 3:
        recommended_offers = random.sample(all_offers, k=3)
    else:
        recommended_offers = all_offers

    pydantic_offers = PydanticOffers.from_orm(recommended_offers)
    dict_offers = pydantic_offers.dict()

    sio.emit("recommended_battles", json.dumps(dict_offers))
    sio.disconnect(sid)


@sio.event
async def accept_offer(sid, data):
    if clients[sid].state == ClientState.logging_in:
        sio.emit("verification_error", "You are not logged in")
        sio.disconnect(sid)

    if not check_passed_data(data, 'user_id', 'nft_id', 'offer_id'):
        sio.emit(
            "wrong_input",
            "You need to pass 'user_id', 'offer_id' and 'nft_id'")
        sio.disconnect(sid)

    accept = Accept()
    accept.user_id = data['user_id']
    accept.nft_id = data['nft_id']
    accept.offer_id = data['offer_id']

    db_sess.add(accept)
    db_sess.commit()

    pydantic_accept = PydanticAccept.from_orm(accept)
    dict_accept = pydantic_accept.dict()

    sio.emit("offer_accept", json.dumps(dict_accept))
    sio.disconnect(sid)


@sio.event
async def accepts_list(sid, data):
    if clients[sid].state == ClientState.logging_in:
        sio.emit("verification_error", "You are not logged in")
        sio.disconnect(sid)

    if not check_passed_data(data, 'offer_id'):
        sio.emit("wrong_input", "You need to pass 'offer_id'")
        sio.disconnect(sid)

    db_sess = database.create_session()

    accepts = db_sess.query(Accept).filter(
        Accept.offer_id == data['offer_id']).all()
    pydantic_accepts = PydanticAccepts.from_orm(accepts)
    dict_accepts = pydantic_accepts.dict()

    sio.emit("accept_list", json.dumps(dict_accepts))
    sio.disconnect(sid)


@sio.event
async def start_battle(sid, data):
    if clients[sid].state == ClientState.logging_in:
        sio.emit("verification_error", "You are not logged in")
        sio.disconnect(sid)

    if not check_passed_data(data, 'offer_id', 'accept_id'):
        sio.emit("wrong_input", "You need to pass 'offer_id' and 'accept_id'")
        sio.disconnect(sid)

    db_sess = database.create_session()

    if db_sess.query(Battle).filter(
            Battle.offer_id == data['offer_id']).first():
        sio.emit("wrong_input", "Battle already started")
        sio.disconnect(sid)

    offer = db_sess.query(Offer).filter(
        Offer.id == data['offer_id']).first()
    accept = db_sess.query(Accept).filter(
        Accept.id == data['accept_id']).first()

    if offer.user_id == accept.user_id:
        sio.emit("wrong_input", "User can't fight himself")
        sio.disconnect(sid)

    battle = Battle()
    battle.offer = offer
    battle.accept = accept
    db_sess.add(battle)
    db_sess.commit()

    pydantic_battle = PydanticBattle.from_orm(battle)
    dict_battle = pydantic_battle.dict()

    sio.emit("created_battle", json.dumps(dict_battle))
    sio.disconnect(sid)


if __name__ == '__main__':
    app = Sanic(name='GameBack')
    sio.attach(app)
    app.run('0.0.0.0', 8080)
