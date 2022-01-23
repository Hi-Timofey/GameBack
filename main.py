from fastapi import FastAPI
from fastapi import HTTPException
import uvicorn
from typing import List
from sqlalchemy.orm import Session

import schemas

from db import database

from db.round import Round
from db.move import Move, Choice
from db.accept import Accept
from db.offer import Offer
from db.battle import Battle


app = FastAPI()


@app.get("/")
async def index():
    return 'Hello, im working'


@app.post("/battles/create", response_model=schemas.Offer)
async def create_offers(offer_json: schemas.Offer):

    db_sess = database.create_session()

    offer_db = Offer()

    offer_db.user_id = offer_json.user_id
    offer_db.nft_id = offer_json.nft_id

    db_sess.add(offer_db)
    db_sess.commit()

    offer_json.id = offer_db.id

    return offer_json


@app.get("/battles/list", response_model=List[schemas.Offer])
async def list_offers():
    db_sess = database.create_session()
    offers = db_sess.query(Offer).all()
    return offers


@app.post("/battles/accept", response_model=schemas.Accept)
async def accept_offer(accept_json: schemas.Accept):
    db_sess = database.create_session()

    accept = Accept()
    accept.user_id = accept_json.user_id
    accept.nft_id = accept_json.nft_id
    accept.offer_id = accept_json.offer_id

    db_sess.add(accept)
    db_sess.commit()

    accept_json.id = accept.id

    return accept_json


@app.post("/battles/start", response_model=schemas.Battle)
async def start_battle(battle_json: schemas.Battle):
    db_sess = database.create_session()

    if db_sess.query(Battle).filter(
            Battle.offer_id == battle_json.offer_id).first():
        raise HTTPException(status_code=400, detail="Battle already started")

    offer = db_sess.query(Offer).filter(Offer.id == battle_json.offer_id).first()
    accept = db_sess.query(Accept).filter(Accept.id == battle_json.accept_id).first()

    if offer.user_id == accept.user_id:
        raise HTTPException(status_code=400, detail="User can't fight himself")

    battle = Battle()
    battle.offer = offer
    battle.accept = accept
    db_sess.add(battle)
    db_sess.commit()

    battle_json.id = battle.id

    return battle_json


@app.post("/battles/move", response_model=schemas.Move)
async def move_battle(move_json: schemas.Move):
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
