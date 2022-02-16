# -*- coding: utf-7 -*-

import logging

import socketio
from sanic import Sanic

import json
from typing import List, Union, Optional
from enum import Enum
from dataclasses import dataclass

# web3
import web3
from web3 import Web3
from eth_account.messages import encode_defunct

# Randomness modules
import uuid
import random

# Database modules
from db import *


def check_passed_data(dic: dict, *names):
    '''
    For checking if correct data passed in event
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
sio = socketio.AsyncServer(async_mode='sanic', cors_allowed_origins='*')

# Connect and disconnect handlers
@sio.event
async def connect(sid, environ):
    logging.info(f'Client {sid} connected')
    session_key = str(uuid.uuid4())
    clients[sid] = Client(sid, session_key)
    await sio.emit("session_key", {"session_key": str(session_key)}, room=sid)


@sio.event
async def disconnect(sid):
    logging.info(f'Client {sid} disconnected')
    del clients[sid]


# Signature auth event
@sio.event
async def verify_signature(sid, data):
    logging.info(f'Client {sid} verifying signature')
    try:
        w3 = Web3()
        clients[sid].address = Web3.toChecksumAddress(data['address'])
        account_recovered = w3.eth.account.recover_message(
            encode_defunct(text=clients[sid].session_key),
            signature=str(data['signature']))
    except Exception as ex:
        return "verification_error", str(ex)

    if clients[sid].address == account_recovered:
        clients[sid].state = ClientState.in_menu
        return "verification_completed", clients[sid].session_key
    else:
        return ("verification_error",
                "Signature address recovered doesn't match the client address")


# Getting list of all battles
@sio.event
async def get_battles_list(sid, data):
    logging.info(f'Client {sid} getting battles list')
    if clients[sid].state == ClientState.logging_in:
        logging.info(f'Client {sid} CONNECTION REFUSED (AUTH)')
        return ('authentication_error', 'You need to log in first')

    try:
        db_sess = database.create_session()
        if 'address' in data.keys():
            battles = db_sess.query(Battle).filter(
                Battle.owner_address == data['address']).all()
        else:
            logging.debug(f'Client {sid} not passed address to get_battles_list')
            return ('wrong_input', 'Address of user not passed')

        dict_battles = []
        for battle in battles:
            pydantic_battle = PydanticBattle.from_orm(battle)
            dict_battle = pydantic_battle.dict()
            dict_battles.append(dict_battle)

        logging.debug(f'Client {sid} getting battles: {dict_battles}')
        return json.dumps(dict_battles)
    except Exception as e:
        info.error("Error in get_battles_list:", exc_info=True)


@sio.event
async def create_battle_offer(sid, data):
    logging.info(f'Client {sid} creating battle offer')
    if clients[sid].state == ClientState.logging_in:
        return ('authentication_error', 'You need to log in first')

    if not check_passed_data(data, 'nft_type', 'nft_id', 'bet'):
        return ("wrong_input", "You need to pass 'bet', 'nft_type' and 'nft_id'")

    db_sess = database.create_session()

    battle = Battle()
    battle.owner_address = clients[sid].address
    battle.nft_id = data['nft_id']
    battle.nft_type = data['nft_type']
    battle.bet = data['bet']
    battle.battle_state = BattleState.listed

    db_sess.add(battle)
    db_sess.commit()

    # Saving creator of the battle ( access by battle_id)
    battles[battle.id] = {'creator': clients[sid],
                          "log": [], "state": BattleState.listed}

    pydantic_battle = PydanticBattle.from_orm(battle)
    dict_battle = pydantic_battle.dict(exclude={'owner_address'})

    # Adding hybrid property to response dict - uri
    # TODO: Make it automatic
    dict_battle['uri'] = battle.uri

    return json.dumps(dict_battle)


@sio.event
async def get_recommended_battles(sid):
    logging.info(f'Client {sid} getting recommended battles')
    if clients[sid].state == ClientState.logging_in:
        logging.info(f'Client {sid} CONNECTION REFUSED (AUTH)')
        return ('authentication_error', 'You need to log in first')

    try:
        db_sess = database.create_session()

        all_offers = db_sess.query(Battle).all()
        if len(all_offers) >= 3:
            recommended_battles = random.sample(all_offers, k=3)
        else:
            recommended_battles = all_offers

        dict_battles = []
        for battle in recommended_battles:
            pydantic_battle = PydanticBattle.from_orm(battle)
            dict_battles.append(pydantic_battle.dict())

        logging.debug(f'Client {sid} getting recommended battles: {dict_battles}')
        return json.dumps(dict_battles)
    except Exception as e:
        info.error("Error in get_battles_list:", exc_info=True)


@sio.event
async def accept_offer(sid, data):
    logging.info(f'Client {sid} accepting offer')
    if clients[sid].state == ClientState.logging_in:
        return ('authentication_error', 'You need to log in first')

    db_sess = database.create_session()

    if not check_passed_data(data, 'nft_id', 'nft_type', 'battle_id'):
        return (
            "wrong_input",
            "You need to pass 'nft_type','nft_id' and 'battle_id'")

    accept = Accept()
    accept.owner_address = clients[sid].address
    accept.nft_id = data['nft_id']
    accept.nft_type = data['nft_type']
    accept.battle_id = data['battle_id']

    db_sess.add(accept)
    db_sess.commit()

    # Saving acceptor (access by accept_id)
    accepts[accept.id] = {"creator": clients[sid]}

    pydantic_accept = PydanticAccept.from_orm(accept)
    dict_accept = pydantic_accept.dict(exclude={'owner_address'})

    return json.dumps(dict_accept)


@sio.event
async def accepts_list(sid, data):
    logging.info(f'Client {sid} getting accepts list')
    if clients[sid].state == ClientState.logging_in:
        return ('authentication_error', 'You need to log in first')

    if not check_passed_data(data, 'battle_id'):
        return ("wrong_input", "You need to pass 'battle_id'")

    db_sess = database.create_session()

    accepts = db_sess.query(Accept).filter(
        Accept.battle_id == data['battle_id']).all()

    dict_accepts = []
    for accept in accepts:
        pydantic_accept = PydanticAccept.from_orm(accept)
        dict_accepts.append(pydantic_accept.dict())

    return json.dumps(dict_accepts)


@sio.event
async def start_battle(sid, data):
    logging.info(f'Client {sid} starting battle')
    if clients[sid].state == ClientState.logging_in:
        return ('authentication_error', 'You need to log in first')

    if not check_passed_data(data, 'battle_id', 'accept_id'):
        return ("wrong_input", "You need to pass 'battle_id' and 'accept_id'")

    db_sess = database.create_session()

    # Check if battle already started
    if db_sess.query(Battle).filter(
            Battle.id == data['battle_id']).first().state == BattleState.in_battle:
        return ("wrong_input", "Battle already started")

    # getting from db all info
    battle = db_sess.query(Battle).filter(
        Battle.id == data['battle_id']).first()
    accept = db_sess.query(Accept).filter(
        Accept.id == data['accept_id']).first()

    # Then gettign sids of both players
    battle_creator_sid = battles[battle.id]['creator']['sid']
    accept_creator_sid = battles[accept.id]['creator']['sid']

    if battle.owner_address == accept.owner_address:
        return ("wrong_input", "User can't fight himself")

    # Commiting that battle started and creator picked opponent
    battle.battle_state = BattleState.in_battle
    battle.accepted_id = accept.id
    db_sess.add(battle)
    db_sess.commit()

    # Both players now IN_BATTLE
    clients[battle_creator_sid].state = ClientState.in_battle
    clients[battle_creator_sid].current_battle = battle.id
    clients[accept_creator_sid].state = ClientState.in_battle
    clients[accept_creator_sid].current_battle = battle.id

    # Saving info about acceptor in battle
    battle[battle.id]['acceptor'] = accept_creator_sid

    # Returning information about created battle (DB)
    pydantic_battle = PydanticBattle.from_orm(battle)
    dict_battle = pydantic_battle.dict()

    await sio.emit("started_battle", json.dumps(dict_battle), room=battle_creator_sid)
    await sio.emit("started_battle", json.dumps(dict_battle), room=accept_creator_sid)
    return json.dumps(dict_battle)


# TODO: Replacing user_id with address
@sio.event
async def make_move(sid, data):
    if clients[sid].state == ClientState.logging_in:
        return ('authentication_error', 'You need to log in first')

    if not check_passed_data(data, 'round', 'choice', 'battle_id'):
        await sio.emit("wrong_input", "You need to pass all args: round, choice, battle_id", room=sid)
        return

    db_sess = database.create_session()

    battle = db_sess.query(Battle).filter(
        Battle.id == data['battle_id']).first()

    if battle is None:
        await sio.emit("wrong_input", "No such battle", room=sid)
        return
    if battle.battle_state == BattleState.listed:
        await sio.emit("wrong_input", "Battle not started", room=sid)
        return

    # Getting info about battle and both players
    battle_info = battles[battle.id]
    first_user_sid = battle_info['creator']
    second_user_sid = battle_info['acceptor']

    if not (first_user_sid == sid or second_user_sid == sid):
        await sio.emit("wrong_input", "Do not participate in this battle", room=sid)
        return

    # Getting local logs and trying to get round if exists
    log_of_battle = battle[battle.id]['log']
    round_of_battle = None
    round_index = -1

    # Local storage not empty - searching round by number
    if log_of_battle != []:
        for round in log_of_battle:
            if round.round_number == data['round']:
                round_of_battle = round
                is_round_new = False
                round_index = log_of_battle.index(round)

    # If no round in local logs - creating round
    if round_of_battle is None:
        round_of_battle = Round()
        round_of_battle.round_number = data['round']
        round_of_battle.battle = battle
        is_round_new = True

    move = Move()
    move.user_id = data['user_id']
    move.choice = data['choice']

    # Adding move to round
    round_of_battle.moves.append(move)

    # Check if enough moves
    if len(round_of_battle.moves) == 2:

        # Player2 is a player who made last move so his sid is in "sid" var
        player1 = round_of_battle.moves[0]  # != sid
        player2 = round_of_battle.moves[1]  # sid

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

    # Guessing winner SID from user_id
    # TODO Simplify
    if round_of_battle.winner_user_id == player2.user_id:
        round_of_battle.winner_sid = sid
    else:
        if sid == first_user_sid:
            round_of_battle.winner_sid = second_user_sid
        else:
            round_of_battle.winner_sid = first_user_sid

    # After checking if we had winner - adding round with moves to local log
    # TODO
    battles[battle.id]['log'][round_index] = round_of_battle

    pydantic_move = PydanticMove.from_orm(move)
    dict_move = pydantic_move.dict()

    await sio.emit("maked_move", json.dumps(dict_move), room=sid)

    # Sending both players event about move.
    if sid == first_user_sid:
        await sio.emit("opponent_maked_move", json.dumps(dict_move), room=second_user_sid)
    else:
        await sio.emit("opponent_maked_move", json.dumps(dict_move), room=first_user_sid)


@sio.event
async def get_battle_log(sid, data):
    # Getting id of battle
    # Returning local storage of rounds
    if clients[sid].state == ClientState.logging_in:
        return ('authentication_error', 'You need to log in first')

    if not check_passed_data(data, 'battle_id'):
        await sio.emit("wrong_input", "You need to pass 'battle_id'", room=sid)
        return

    db_sess = database.create_session()

    battle_id = data['battle_id']
    battle = db_sess.query(Battle).filter(Battle.id == battle_id).first()

    if battle.log == []:
        battle_log = battles[battle.id]['log']
    else:
        battle_log = battle.log

    dict_log = []
    for round in battle_log:
        pydantic_round = PydanticRound.from_orm(round)
        dict_log.append(pydantic_round.dict())

    # TODO: Returning winner_user_id=NULL on not finished round
    await sio.emit("battle_log", json.dumps(dict_log), room=sid)


if __name__ == '__main__':
    app = Sanic(name='GameBack')
    sio.attach(app)

    logging.basicConfig(
        # filename='app.log',
                    filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s | %(levelname)s - %(message)s')

    app.run('0.0.0.0', 8080)
