import socketio
from socketio.exceptions import ConnectionRefusedError
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
from db import *


def check_passed_data(dic: dict, *names):
    ''' For checking if correct data passed in event
    dic - pass data from event
    names - which args must be in data
    '''
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
    sid: str
    session_key: str
    address: str = ''
    state: ClientState = ClientState.logging_in
    current_battle: int = -1


# Client connection data
clients = {}
# Memory battlers sids
battles = {}
accepts = {}

database.global_init_sqlite('db.sqlite')
sio = socketio.AsyncServer(async_mode='sanic')

# Connect and disconnect handlers


@sio.event
async def connect(sid, environ, auth):
    print(f'Client {sid} connected')
    session_key = uuid.uuid4()
    clients[sid] = Client(sid, session_key)
    await sio.emit("session_key", {"session_key": str(session_key)}, room=sid)


@sio.event
async def disconnect(sid):
    print(f'Client {sid} disconnected')
    del clients[sid]
    await sio.emit("disconnected")
    sio.disconnect(sid)


# Signature auth event
@sio.event
async def verify_signature(sid, data):
    try:
        clients[sid].address = data['address']
        account_recovered = Web3.eth.account.recover_message(
            encode_defunct(text=clients[sid].session_key),
            signature=str(data['signature']))
    except Exception as ex:
        await sio.emit("verification_error", str(ex))
        sio.disconnect(sid)

    if clients[sid].address == account_recovered:
        clients[sid].state = ClientState.in_menu
    else:
        await sio.emit(
            "verification_error",
            "Signature address recovered doesn't match the client address")
        sio.disconnect(sid)


# Getting list of all battles
@sio.event
async def get_battles_list(sid, data):
    if clients[sid].state == ClientState.logging_in:
        raise ConnectionRefusedError('authentication failed')

    db_sess = database.create_session()
    if data['user_id']:
        battles = db_sess.query(Battle).filter(
            Battle.user_id == data['user_id']).all()
    else:
        battles = db_sess.query(Battle).all()

    if battles == []:
        await sio.emit("battles_list", json.dumps(battles), room=sid)
        return

    dict_battles = []
    for battle in battles:
        pydantic_battle = PydanticBattle.from_orm(battle)
        dict_battle = pydantic_battle.dict()
        dict_battles.append(dict_battle)

    await sio.emit("battles_list", json.dumps(dict_battles), room=sid)


@sio.event
async def create_battle_offer(sid, data):
    if clients[sid].state == ClientState.logging_in:
        raise ConnectionRefusedError('authentication failed')

    if not check_passed_data(data, 'user_id', 'nft_id'):
        await sio.emit("wrong_input", "You need to pass 'user_id' and 'nft_id'", room=sid)
        sio.disconnect(sid)

    db_sess = database.create_session()

    battle = Battle()

    battle.user_id = data['user_id']
    battle.nft_id = data['nft_id']
    battle.battle_state = BattleState.listed

    db_sess.add(battle)
    db_sess.commit()

    # Saving creator of the battle ( access by battle_id)
    battles[battle.id] = {'creator': client[sid],
                          "log": [], "state": BattleState.listed}

    pydantic_battle = PydanticBattle.from_orm(battle)
    dict_battle = pydantic_battle.dict()

    await sio.emit("created_battle", json.dumps(dict_battle), room=sid)


@sio.event
async def get_recommended_battles(sid):
    if clients[sid].state == ClientState.logging_in:
        raise ConnectionRefusedError('authentication failed')

    db_sess = database.create_session()

    all_offers = db_sess.query(Battle).all()
    if len(all_offers) >= 3:
        recommended_battles = random.sample(all_offers, k=3)
    else:
        recommended_battles = all_offers

    if recommended_battles == []:
        await sio.emit("recommended_battles", json.dumps(recommended_battles), room=sid)
        return

    dict_battles = []
    for battle in recommended_battles:
        pydantic_battle = PydanticBattle.from_orm(battle)
        dict_battle.append(pydantic_battle.dict())

    await sio.emit("recommended_battles", json.dumps(dict_battle), room=sid)


@sio.event
async def accept_offer(sid, data):
    if clients[sid].state == ClientState.logging_in:
        raise ConnectionRefusedError('authentication failed')

    if not check_passed_data(data, 'user_id', 'nft_id', 'battle_id'):
        await sio.emit(
            "wrong_input",
            "You need to pass 'user_id', 'battle_id' and 'nft_id'", room=sid)

    accept = Accept()
    accept.user_id = data['user_id']
    accept.nft_id = data['nft_id']
    accept.battle_id = data['battle_id']

    db_sess.add(accept)
    db_sess.commit()

    # Saving acceptor (access by accept_id)
    accepts[accept.id] = {"creator": client["sid"]}

    pydantic_accept = PydanticAccept.from_orm(accept)
    dict_accept = pydantic_accept.dict()

    await sio.emit("added_accept_to_battle", json.dumps(dict_accept), room=sid)


@sio.event
async def accepts_list(sid, data):
    if clients[sid].state == ClientState.logging_in:
        raise ConnectionRefusedError('authentication failed')

    if not check_passed_data(data, 'battle_id'):
        await sio.emit("wrong_input", "You need to pass 'battle_id'", room=sid)
        sio.disconnect(sid)

    db_sess = database.create_session()

    accepts = db_sess.query(Accept).filter(
        Accept.battle_id == data['battle_id']).all()

    if accepts == []:
        await sio.emit("accepts", json.dumps([]), room=sid)
        return

    dict_accepts = []
    for accept in accepts:
        pydantic_accept = PydanticAccept.from_orm(accept)
        dict_accepts.append(pydantic_accept.dict())

    await sio.emit("accept_list", json.dumps(dict_accepts), room=sid)


@sio.event
async def start_battle(sid, data):
    if clients[sid].state == ClientState.logging_in:
        raise ConnectionRefusedError('authentication failed')

    if not check_passed_data(data, 'battle_id', 'accept_id'):
        await sio.emit("wrong_input", "You need to pass 'battle_id' and 'accept_id'", room=sid)
        sio.disconnect(sid)

    db_sess = database.create_session()

    # Check if battle already started
    if db_sess.query(Battle).filter(
            Battle.id == data['battle_id']).first().state == BattleState.in_battle:
        await sio.emit("wrong_input", "Battle already started", room=sid)
        return

    # getting from db all info
    battle = db_sess.query(Battle).filter(
        Battle.id == data['battle_id']).first()
    accept = db_sess.query(Accept).filter(
        Accept.id == data['accept_id']).first()

    # Then gettign sids of both players
    battle_creator_sid = battles[battle.id]['creator']['sid']
    accept_creator_sid = battles[accept.id]['creator']['sid']

    if battle.user_id == accept.user_id:
        await sio.emit("wrong_input", "User can't fight himself", room=sid)
        return

    # Commiting that battle started and creator picked opponent
    battle = Battle()
    battle.battle_state = BattleState.in_battle
    battle.accepted_id = accept.id
    db_sess.add(battle)
    db_sess.commit()

    # Both players now IN_BATTLE
    clients[battle_creator_sid].state = ClientState.in_battle
    clients[battle_creator_sid].current_battle = battle.id
    clients[accept_creator_sid].state = ClientState.in_battle
    clients[accept_creator_sid].current_battle = battle.id

    # Saving in battle info about acceptor
    battle[battle.id]['acceptor'] = accept_creator_sid

    # Returning information about created battle (DB)
    pydantic_battle = PydanticBattle.from_orm(battle)
    dict_battle = pydantic_battle.dict()

    await sio.emit("started_battle", json.dumps(dict_battle), room=battle_creator_sid)
    await sio.emit("started_battle", json.dumps(dict_battle), room=accept_creator_sid)


@sio.event
async def make_move(sid, data):
    if clients[sid].state == ClientState.logging_in:
        raise ConnectionRefusedError('authentication failed')

    if not check_passed_data(data, 'user_id', 'round', 'choice', 'battle_id'):
        await sio.emit("wrong_input", "You need to pass all args", room=sid)
        return

    db_sess = database.create_session()

    battle = db_sess.query(Battle).filter(
        Battle.id == data['battle_id']).first()

    if battle is None:
        await sio.emit("wrong_input", "No such battle", room=sid)
        return

    # Getting info about battle and both players
    battle_info = battles[battle.id]
    first_user_sid = battle_info['creator']
    second_user_sid = battle_info['acceptor']

    if first_user_sid == second_user_sid:
        await sio.emit("wrong_input", "Can not beat yourself", room=sid)
        return

    if not (first_user_sid == sid or second_user_sid == sid):
        await sio.emit("wrong_input", "Do not participate in this battle", room=sid)
        return

    # Getting local logs and trying to get round if exists
    log_of_battle = battle[battle.id]['log']
    round_of_battle = None

    if log_of_battle != []:
        # Local storage not empty - seaching round by number
        for round in log_of_battle:
            if round.round_number == data['round']:
                round_of_battle = round

    # If no round in local logs - creating round
    if round_of_battle is None:
        round_of_battle = Round()
        round_of_battle.round_number = data['round']
        round_of_battle.battle = battle

    move = Move()
    move.user_id = data['user_id']
    move.choice = data['choice']

    # Adding move to round
    round_of_battle.moves.append(move)

    # Check if the opponent has made a move
    if len(round_of_battle.moves) == 2:
        player1 = round_of_battle.moves[0]
        player2 = round_of_battle.moves[1]

        # Game logic
        if player1.choice == player2.choice:
            round_of_battle.winner_user_id = 0

        elif player1.choice == Choice.rock:
            if player2.choice == Choice.scissors:
                round_of_battle.winner_user_id = player1.user_id
            else:
                round_of_battle.winner_user_id = player2.user_id
        elif player1.choice == Choice.paper:
            if player2.choice == Choice.rock:
                round_of_battle.winner_user_id = player1.user_id
            else:
                round_of_battle.winner_user_id = player2.user_id
        elif player1.choice == Choice.scissors:
            if player2.choice == Choice.paper:
                round_of_battle.winner_user_id = player1.user_id
            else:
                round_of_battle.winner_user_id = player2.user_id

    # After checking if we had winner - adding round with moves to local log
    battles[battle.id]['log'].append(round_of_battle)
    await sio.emit("maked_move", json.dumps(dict_battle), room=sid)

    # TODO: Sending both players event about move. need to rework (?)
    if sid == first_user_sid:
        await sio.emit("opponent_maked_move", json.dumps(dict_battle), room=second_user_sid)
    else:
        await sio.emit("opponent_maked_move", json.dumps(dict_battle), room=first_user_sid)


if __name__ == '__main__':
    app = Sanic(name='GameBack')
    sio.attach(app)
    app.run('0.0.0.0', 8080)
