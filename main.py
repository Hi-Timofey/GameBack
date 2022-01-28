from fastapi import FastAPI
from fastapi import Response, status, HTTPException, Cookie
import uvicorn
from typing import List, Union, Optional
from sqlalchemy.orm import Session
import web3

import uuid

import schemas

from db import database

from db.session_keys import SessionKey
from db.round import Round
from db.move import Move, Choice
from db.accept import Accept
from db.offer import Offer
from db.battle import Battle


app = FastAPI()


@app.get("/")
async def index():
    return 'Hello, im working'


@app.post("/login")
async def index(response: Response, json: schemas.LoginAddress, session_key: Optional[str] = Cookie(None)):
    db_sess = database.create_session()
    address = json.address
    random_string = uuid.uuid4()

    session_key = SessionKey(
        session_key=random_string,
        user_address=address,
    )

    db_sess.add(SessionKey)
    db_sess.commit()

    response.status_code = status.HTTP_201_CREATED
    response.set_cookie(key="session_key", value=random_string)
    return {'session_key': random_string}


@app.post("/signature")
async def index(response: Response, json: schemas.LoginSigned, session_key: Optional[str] = Cookie(None)):
    db_sess = database.create_session()
    w3 = web3.Web3()
    signed_key = json.signed
    account_recovered = w3.eth.account.recover_message(
        signed_key, signature=session_key)

    breakpoint()

    session = db_sess.query(SessionKey).filter(
        SessionKey.session_key == session_key).first()

    if session.user_address == account_recovered:
        session.verified = True
        db_sess.add(session)
        db_sess.commit()
        return 'verified'
    else:
        return "not verified"


@app.post("/battles/create", response_model=schemas.Offer)
async def create_offers(offer_json: schemas.Offer, response: Response):

    db_sess = database.create_session()

    offer_db = Offer()

    offer_db.user_id = offer_json.user_id
    offer_db.nft_id = offer_json.nft_id

    db_sess.add(offer_db)
    db_sess.commit()

    offer_json.id = offer_db.id

    response.status_code = status.HTTP_201_CREATED
    return offer_json


@app.get("/battles/list", response_model=List[schemas.Offer])
async def list_offers():
    db_sess = database.create_session()
    offers = db_sess.query(Offer).all()
    return offers


@app.post("/battles/accept", response_model=schemas.Accept)
async def accept_offer(accept_json: schemas.Accept, response: Response):
    db_sess = database.create_session()

    accept = Accept()
    accept.user_id = accept_json.user_id
    accept.nft_id = accept_json.nft_id
    accept.offer_id = accept_json.offer_id

    db_sess.add(accept)
    db_sess.commit()

    accept_json.id = accept.id

    response.status_code = status.HTTP_201_CREATED
    return accept_json


@app.post("/battles/start", response_model=schemas.Battle)
async def start_battle(battle_json: schemas.Battle, response: Response):
    db_sess = database.create_session()

    if db_sess.query(Battle).filter(
            Battle.offer_id == battle_json.offer_id).first():
        raise HTTPException(status_code=400, detail="Battle already started")

    offer = db_sess.query(Offer).filter(
        Offer.id == battle_json.offer_id).first()
    accept = db_sess.query(Accept).filter(
        Accept.id == battle_json.accept_id).first()

    if offer.user_id == accept.user_id:
        raise HTTPException(status_code=400, detail="User can't fight himself")

    battle = Battle()
    battle.offer = offer
    battle.accept = accept
    db_sess.add(battle)
    db_sess.commit()

    battle_json.id = battle.id

    response.status_code = status.HTTP_201_CREATED
    return battle_json


@app.post("/battles/move", response_model=schemas.Move)
async def move_battle(move_json: schemas.Move, response: Response):
    db_sess = database.create_session()

    battle = db_sess.query(Battle).filter(
        Battle.id == move_json.battle_id).first()

    if battle is None:
        raise HTTPException(status_code=400, detail="Battle not found")

    first_user_id = battle.offer.user_id
    second_user_id = battle.accept.user_id

    if first_user_id == second_user_id:
        raise HTTPException(status_code=400, detail="User can't fight himself")

    if not (first_user_id == move_json.user_id or second_user_id
            == move_json.user_id):
        raise HTTPException(
            status_code=400,
            detail="User does not participate in this battle")

    breakpoint()

    round_of_battle = db_sess.query(Round).filter(
        Round.battle_id == battle.id and Round.round_number == move_json.round
    ).first()

    if round_of_battle is None:
        round_of_battle = Round()
        round_of_battle.round_number = move_json.round
        round_of_battle.battle = battle

    move = Move()
    move.user_id = move_json.user_id
    move.choice = move_json.choice

    round_of_battle.moves.append(move)

    db_sess.add(round_of_battle)
    db_sess.commit()

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

        db_sess.add(round_of_battle)
        db_sess.commit()

    move_json.id = move.id
    move_json.choice = move.choice.value

    response.status_code = status.HTTP_201_CREATED
    return move_json


@app.get("/battles/log", response_model=List[schemas.Round])
async def get_battle_log(json: schemas.BattleId):

    db_sess = database.create_session()

    battle_id = json.battle_id

    battle = db_sess.query(Battle).filter(Battle.id == battle_id).first()

    # TODO: Returning winner_user_id=NULL on not finished round
    return battle.log


if __name__ == "__main__":
    database.global_init_sqlite('db.sqlite')
    uvicorn.run(app, host="0.0.0.0", port=8000)
