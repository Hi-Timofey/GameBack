import logging
import time
import asyncio
import socketio  # type: ignore

from fastapi import FastAPI
import uvicorn


import json
from dataclasses import dataclass
from eth_account.messages import encode_defunct

# Randomness modules
import uuid
import random

# Database modules
from db import *  # noqa


def check_passed_data(dic: dict, *names):
    """
    For checking if correct data passed in event
    dic - pass data from event
    names - which args must be in data
    """
    for name in names:
        if name not in dic:
            return False
    return True


# Client states possible
class ClientState(Enum):  # noqa
    logging_in = 1
    in_menu = 2
    in_battle = 3


# Client connection data
# TODO: change to sio.save_session
clients = {}  # type: ignore


@dataclass
class Client:
    sid: str
    session_key: str
    address: str = ""
    state: ClientState = ClientState.logging_in  # type: ignore
    current_battle: int = -1

    def get_sid_by_address(address) -> str:
        global clients
        if address == "no_one":
            return "no_one"
        for sid in clients:
            if clients[sid].address == address:
                return sid
        raise ValueError(f"Not found client with address {address}")


# Memory battlers sids
# BATTLES: 'creator', 'log', 'state'
battles = {}  # type: ignore
accepts = {}

database.global_init_sqlite("db.sqlite")  # type: ignore # noqa
sio = socketio.AsyncServer(async_mode="asgi")

# Connect and disconnect handlers


@sio.event
async def connect(sid, environ):
    logging.info(f"Client {sid} connected")
    session_key = str(uuid.uuid4())
    clients[sid] = Client(sid, session_key)
    await sio.emit("session_key", {"session_key": str(session_key)}, room=sid)


@sio.event
async def disconnect(sid):
    logging.info(f"Client {sid} disconnected")

    db_sess = database.create_session()  # noqa
    to_delete_ind = []
    try:
        lock = asyncio.Lock()
        async with lock:
            del clients[sid]
            for battle_id in battles:
                battle_info = battles[battle_id]
                if (
                    battle_info["creator"].sid == sid
                    and battle_info["state"] == BattleState.listed  # noqa
                ):  # noqa
                    battle_db = (
                        db_sess.query(Battle)  # noqa
                        .filter(Battle.id == battle_id)  # noqa
                        .first()
                    )  # noqa
                    db_sess.delete(battle_db)
                    db_sess.commit()
                    to_delete_ind.append(battle_id)

                if (
                    battle_info["creator"].sid == sid
                    and battle_info["state"] == BattleState.ended  # noqa
                ):  # noqa
                    to_delete_ind.append(battle_id)
            for battle_id in to_delete_ind:
                del battles[battle_id]
    except BaseException as be:
        logging.warning(f"{be} coused after {sid} disconnected")


# Signature auth event
@sio.event
async def verify_signature(sid, data):
    logging.info(f"Client {sid} verifying signature")
    try:
        w3 = Web3()  # noqa
        clients[sid].address = Web3.toChecksumAddress(data["address"])  # noqa
        account_recovered = w3.eth.account.recover_message(
            encode_defunct(text=clients[sid].session_key),
            signature=str(data["signature"]),
        )
    except Exception as ex:
        return "verification_error", str(ex)

    if clients[sid].address == account_recovered:
        clients[sid].state = ClientState.in_menu
        return "verification_completed", clients[sid].session_key
    else:
        return (
            "verification_error",
            "Signature address recovered doesn't match the client address",
        )


# Getting list of all battles
@sio.event
async def get_battles_list(sid, data):
    logging.info(f"Client {sid} getting battles list")
    if clients[sid].state == ClientState.logging_in:
        logging.info(f"Client {sid} CONNECTION REFUSED (AUTH)")
        return ("authentication_error", "You need to log in first")

    try:
        db_sess = database.create_session()  # noqa
        if "address" in data.keys():
            address = Web3.toChecksumAddress(data["address"])  # noqa
            logging.debug(f"Client {sid} getting battles of {address}")
            battles = (
                db_sess.query(Battle)  # noqa
                .filter(Battle.owner_address == address)  # noqa
                .all()
            )  # noqa
        else:
            logging.debug(f"Client {sid} not passed address to get_battles_list")
            return ("wrong_input", "Address of user not passed")

        dict_battles = []
        for battle in battles:
            pydantic_battle = PydanticBattle.from_orm(battle)  # noqa
            dict_battle = pydantic_battle.dict()
            dict_battle["uri"] = battle.uri
            dict_battles.append(dict_battle)

        logging.debug(f"Client {sid} getting battles: {dict_battles}")
        return json.dumps(dict_battles)
    except Exception as e:  # noqa
        logging.error("Error in get_battles_list:", exc_info=True)


@sio.event
async def create_battle_offer(sid, data):
    logging.info(f"Client {sid} creating battle offer")
    if clients[sid].state == ClientState.logging_in:
        return ("authentication_error", "You need to log in first")

    if not check_passed_data(data, "nft_type", "nft_id", "bet"):
        return ("wrong_input", "You need to pass 'bet', 'nft_type' and 'nft_id'")

    db_sess = database.create_session()  # noqa

    battle = Battle()  # noqa
    battle.owner_address = clients[sid].address
    battle.nft_id = data["nft_id"]
    battle.nft_type = data["nft_type"]
    battle.bet = data["bet"]
    battle.battle_state = BattleState.listed  # noqa

    db_sess.add(battle)
    db_sess.commit()

    # Saving creator of the battle ( access by battle_id)
    battles[battle.id] = {
        "creator": clients[sid],
        "log": [],
        "state": BattleState.listed,  # noqa
    }  # noqa

    pydantic_battle = PydanticBattle.from_orm(battle)  # noqa
    dict_battle = pydantic_battle.dict(exclude={"owner_address"})

    # Adding hybrid property to response dict - uri
    dict_battle["uri"] = battle.uri

    return json.dumps(dict_battle)


@sio.event
async def get_recommended_battles(sid):
    logging.info(f"Client {sid} getting recommended battles")
    if clients[sid].state == ClientState.logging_in:
        logging.info(f"Client {sid} CONNECTION REFUSED (AUTH)")
        return ("authentication_error", "You need to log in first")

    try:
        db_sess = database.create_session()  # noqa

        all_offers = (
            db_sess.query(Battle)  # noqa
            .filter(Battle.owner_address != clients[sid].address)  # noqa
            .filter(Battle.battle_state == BattleState.listed)  # noqa
            .all()
        )  # noqa
        if len(all_offers) >= 3:
            recommended_battles = random.sample(all_offers, k=3)
        else:
            recommended_battles = all_offers

        dict_battles = []
        for battle in recommended_battles:
            pydantic_battle = PydanticBattle.from_orm(battle)  # noqa
            dict_battle = pydantic_battle.dict()
            dict_battle["uri"] = battle.uri
            dict_battles.append(dict_battle)

        logging.debug(f"Client {sid} getting recommended battles: {dict_battles}")
        return json.dumps(dict_battles)
    except Exception as e:  # noqa
        logging.error("Error in get_battles_list:", exc_info=True)


@sio.event
async def accept_offer(sid, data):  # noqa
    logging.info(f"Client {sid} accepting offer")
    if clients[sid].state == ClientState.logging_in:
        return ("authentication_error", "You need to log in first")

    db_sess = database.create_session()  # noqa

    if not check_passed_data(data, "nft_id", "nft_type", "battle_id"):
        return ("wrong_input", "You need to pass 'nft_type','nft_id' and 'battle_id'")

    battle = (
        db_sess.query(Battle).filter(Battle.id == data["battle_id"]).first()  # noqa
    )  # noqa
    if battle is None:
        logging.debug(
            f'Client {sid} accepting not existing battle with id: {data["battle_id"]}'
        )
        return ("wrong_input", "No such battle")

    if battle.owner_address == clients[sid].address:
        logging.debug(f"Client {sid} accepting self created battle")
        return ("wrong_input", "Can not fight yourself")

    if battle.battle_state != BattleState.listed:  # noqa
        return ("wrong_input", "Battle already started")

    accept = Accept()  # noqa
    accept.owner_address = clients[sid].address
    accept.nft_id = data["nft_id"]
    accept.nft_type = data["nft_type"]
    accept.battle = battle

    db_sess.add(accept)
    db_sess.flush()
    db_sess.commit()

    # TODO: Issue with disconnection of users must be fixed
    try:
        creator_sid = battles[battle.id]["creator"].sid
    except BaseException:
        owner_address = battle.owner_address
        creator_sid = None
        for sid in clients:
            if clients[sid].address == owner_address:
                creator_sid = sid
        if creator_sid is None:
            return ("error", f"Can not find such battle with id {battle.id}")

    # Saving acceptor (access by accept_id)
    accepts[accept.id] = {"creator": clients[sid]}

    pydantic_accept = PydanticAccept.from_orm(accept)  # noqa
    dict_accept = pydantic_accept.dict()

    dict_accept["uri"] = accept.uri
    dict_accept["bet"] = battle.bet

    await sio.emit("accept_added", json.dumps(dict_accept), room=creator_sid)
    return json.dumps(dict_accept)


@sio.event
async def accepts_list(sid, data):
    logging.info(f"Client {sid} getting accepts list")
    if clients[sid].state == ClientState.logging_in:
        return ("authentication_error", "You need to log in first")

    if not check_passed_data(data, "battle_id"):
        return ("wrong_input", "You need to pass 'battle_id'")

    db_sess = database.create_session()  # noqa

    accepts = (
        db_sess.query(Accept)  # noqa
        .filter(Accept.battle_id == data["battle_id"])  # noqa
        .all()
    )  # noqa

    dict_accepts = []
    for accept in accepts:
        pydantic_accept = PydanticAccept.from_orm(accept)  # noqa
        dict_accepts.append(pydantic_accept.dict())

    return json.dumps(dict_accepts)


@sio.event
async def start_battle(sid, data):  # noqa
    if clients[sid].state == ClientState.logging_in:
        return ("authentication_error", "You need to log in first")

    if not check_passed_data(data, "battle_id", "accept_id"):
        return ("wrong_input", "You need to pass 'battle_id' and 'accept_id'")

    db_sess = database.create_session()  # noqa
    # Getting battle and accept from DB
    battle = (
        db_sess.query(Battle).filter(Battle.id == data["battle_id"]).first()  # noqa
    )  # noqa
    if battle is None:
        return ("wrong_input", "Battle not found")

    accept = (
        db_sess.query(Accept).filter(Accept.id == data["accept_id"]).first()  # noqa
    )  # noqa
    if accept is None:
        return ("wrong_input", "Accept not found")

    # Check if battle already started
    if battle.battle_state == BattleState.in_battle:  # noqa
        return ("wrong_input", "Battle already started")
    if battle.owner_address == accept.owner_address:
        return ("wrong_input", "User can't fight himself")

    # Then gettign sids of both players
    battle_creator = battles[battle.id]["creator"]
    accept_creator = accepts[accept.id]["creator"]

    if battle_creator.sid == accept_creator.sid:
        return ("wrong_input", "User can't fight himself")

    logging.info(f"Client {sid} starting battle with {accept_creator.sid}")

    # Commiting that battle started and creator picked opponent
    battle.battle_state = BattleState.in_battle  # noqa
    battle.accepted_id = accept.id
    db_sess.add(battle)
    db_sess.commit()

    # Both players now IN_BATTLE
    clients[battle_creator.sid].state = ClientState.in_battle
    clients[battle_creator.sid].current_battle = battle.id
    clients[accept_creator.sid].state = ClientState.in_battle
    clients[accept_creator.sid].current_battle = battle.id

    # Saving info about acceptor in battle
    battles[battle.id]["acceptor"] = accept_creator
    battles[battle.id]["creator_hp"] = 100
    battles[battle.id]["acceptor_hp"] = 100

    first_round = Round()  # noqa
    first_round.round_number = 1
    first_round.battle = battle
    battles[battle.id]["log"].append(first_round)

    for a in battle.accepts:
        if a.id != battle.accepted_id:
            await sio.emit(
                "battle_canceled",
                {"battle_id": battle.id},
                room=Client.get_sid_by_address(a.owner_address),
            )

    # Returning information about created battle (DB)
    pydantic_battle = PydanticBattle.from_orm(battle)  # noqa
    dict_battle = pydantic_battle.dict()

    await sio.emit("started_battle", json.dumps(dict_battle), room=accept_creator.sid)
    # await sio.start_background_task(round_timeout, (battle.id))
    return json.dumps(dict_battle)


async def round_timeout(battle_id):
    logging.debug("timeout function started working")
    # await sio.sleep(seconds=5.5)
    time.sleep(10)
    logging.debug("timeout for move")

    battle_info = battles[battle_id]
    round_of_battle = battle_info["log"][-1]
    logging.debug(f"ROUND: {round_of_battle}")
    creator_info = battle_info["creator"]
    acceptor_info = battle_info["acceptor"]

    if len(round_of_battle.moves) == 1:
        logging.debug("1 random move")
        random_move = Move()  # noqa
        random_move.round_id = round_of_battle.id
        random_move.choice = random.choice(list(Choice))  # noqa # nosec
        if round_of_battle.moves[0].owner_address == creator_info.address:
            random_move.owner_address == acceptor_info.address
        else:
            random_move.owner_address == creator_info.address
        round_of_battle.moves.append(random_move)
    elif len(round_of_battle.moves) == 0:
        logging.debug("2 random move")
        first_move = Move()  # noqa
        first_move.round_id = round_of_battle.id
        first_move.choice = random.choice(list(Choice))  # noqa # nosec
        first_move.owner_address = creator_info.address
        round_of_battle.moves.append(first_move)

        second_move = Move()  # noqa
        second_move.round_id = round_of_battle.id
        second_move.choice = random.choice(list(Choice))  # noqa # nosec
        second_move.owner_address = acceptor_info.address
        round_of_battle.moves.append(second_move)
    else:
        logging.debug("0 random move (round completed)")
    round_of_battle.set_winner_user_address()
    round_of_battle.winner_sid = Client.get_sid_by_address(
        round_of_battle.winner_user_address
    )
    battles[battle_id]["log"][-1] = round_of_battle
    await emit_ended_round(round_of_battle, creator_info, acceptor_info)
    return


async def emit_ended_round(
    round_of_battle, creator_info: Client, acceptor_info: Client
):
    battle = round_of_battle.battle
    if round_of_battle.winner_sid == creator_info.sid:
        battles[battle.id]["acceptor_hp"] -= 30
    elif round_of_battle.winner_sid == acceptor_info.sid:
        battles[battle.id]["creator_hp"] -= 30

    # End of round event
    await sio.emit(
        "round_ended",
        {
            "left_choice": round_of_battle.get_move_of_address(
                creator_info.address
            ).choice,
            "right_choice": round_of_battle.get_move_of_address(
                acceptor_info.address
            ).choice,
            "left_hp": battles[battle.id]["creator_hp"],
            "right_hp": battles[battle.id]["acceptor_hp"],
        },
        room=creator_info.sid,
    )

    await sio.emit(
        "round_ended",
        {
            "left_choice": round_of_battle.get_move_of_address(
                acceptor_info.address
            ).choice,
            "right_choice": round_of_battle.get_move_of_address(
                creator_info.address
            ).choice,
            "left_hp": battles[battle.id]["acceptor_hp"],  # acceptor
            "right_hp": battles[battle.id]["creator_hp"],
        },  # creator
        room=acceptor_info.sid,
    )


@sio.event
async def make_move(sid, data):  # noqa
    if clients[sid].state == ClientState.logging_in:
        return ("authentication_error", "You need to log in first")

    if not check_passed_data(data, "choice"):
        return ("wrong_input", "You need to pass choice")

    db_sess = database.create_session()  # noqa
    battle_id = clients[sid].current_battle
    if battle_id is None:
        return ("wrong_input", "No related to user battle found")

    battle = (
        db_sess.query(Battle).filter(Battle.id == battle_id).first()  # noqa
    )  # noqa

    if battle is None:
        return ("wrong_input", "No such battle")
    if battle.battle_state != BattleState.in_battle:  # noqa
        return ("wrong_input", "Battle not started")

    # Getting info about battle and both players
    battle_info = battles[battle.id]
    creator_info = battle_info["creator"]
    acceptor_info = battle_info["acceptor"]

    if not (creator_info.sid == sid or acceptor_info.sid == sid):
        return ("wrong_input", "You do not participate in this battle")

    # Getting local logs and trying to get round if exists
    log_of_battle = battle_info["log"]

    # Round with one move - getting
    # Round with two moves - create another one
    if len(log_of_battle[-1].moves) == 2:
        round_of_battle = Round()  # noqa
        round_of_battle.round_number = len(log_of_battle) + 1
        round_of_battle.battle = battle
        is_round_new = True
    elif len(log_of_battle[-1].moves) <= 1:
        round_of_battle = log_of_battle[-1]
        is_round_new = False

    move = Move()  # noqa
    move.owner_address = clients[sid].address
    move.choice = data["choice"]

    # Adding move to round
    round_of_battle.moves.append(move)

    # Check if enough moves
    if len(round_of_battle.moves) == 2:

        # Player2 is a player who made last move so his sid is in "sid" var
        player1 = round_of_battle.moves[0]  # != sid
        player2 = round_of_battle.moves[1]  # sid

        # Game logic
        if player1.choice == player2.choice:
            round_of_battle.winner_user_address = "no_one"
            round_of_battle.winner_sid = "no_one"
        else:
            if player1.choice == Choice.attack:  # noqa
                if player2.choice == Choice.trick:  # noqa
                    round_of_battle.winner_user_address = player1.owner_address
                else:
                    round_of_battle.winner_user_address = player2.owner_address
            elif player1.choice == Choice.trick:  # noqa
                if player2.choice == Choice.block:  # noqa
                    round_of_battle.winner_user_address = player1.owner_address
                else:
                    round_of_battle.winner_user_address = player2.owner_address
            elif player1.choice == Choice.block:  # noqa
                if player2.choice == Choice.attack:  # noqa
                    round_of_battle.winner_user_address = player1.owner_address
                else:
                    round_of_battle.winner_user_address = player2.owner_address
            round_of_battle.winner_sid = Client.get_sid_by_address(
                round_of_battle.winner_user_address
            )

    # If there is a winner - emitting end of round
    if round_of_battle.winner_user_address is not None:
        await emit_ended_round(round_of_battle, creator_info, acceptor_info)
        return

    # After checking if we had winner - adding round with moves to local log
    if is_round_new:
        battles[battle.id]["log"].append(round_of_battle)
        # await sio.start_background_task(round_timeout, (battle_id))
    else:
        battles[battle.id]["log"][-1] = round_of_battle

    # Sending both players event about move.
    # if sid == creator_info.sid:
    #     await sio.emit("opponent_maked_move", 'Your opponmove has made a move', room=acceptor_info.sid)
    # else:
    # await sio.emit("opponent_maked_move", 'Your opponmove has made a move',
    # room=creator_info.sid)
    return ("maked_move", "Your move is registered")


@sio.event
async def get_battle_log(sid, data):
    # Getting id of battle
    # Returning local storage of rounds
    if clients[sid].state == ClientState.logging_in:
        return ("authentication_error", "You need to log in first")

    if not check_passed_data(data, "battle_id"):
        return ("wrong_input", "You need to pass 'battle_id'")

    db_sess = database.create_session()  # noqa

    battle_id = data["battle_id"]
    battle = db_sess.query(Battle).filter(Battle.id == battle_id).first()  # noqa

    if battle.log == []:
        battle_log = battles[battle.id]["log"]
    else:
        battle_log = battle.log

    dict_log = []
    for round in battle_log:
        pydantic_round = PydanticRound.from_orm(round)  # noqa
        dict_log.append(pydantic_round.dict())

    # TODO: Returning winner_user_id=NULL on not finished round
    return json.dumps(dict_log)


app = FastAPI()

app.mount("/sio", socketio.ASGIApp(sio))

if __name__ == "__main__":

    logging.basicConfig(
        # filename='app.log',
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s - %(message)s",
    )

    uvicorn.run(app, port=80)
