from fastapi import FastAPI
from fastapi import HTTPException
import uvicorn
from typing import List
from sqlalchemy.orm import Session

import schemas

from db import database

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

    battle = Battle()
    battle.offer_id = battle_json.offer_id
    battle.accept_id = battle_json.accept_id
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
    second_user_id = battle.offer.user_id

    if not (first_user_id == move_json.user_id or second_user_id
            == move_json.user_id):
        raise HTTPException(
            status_code=400,
            detail="User does not participate in this battle")

    move = Move()
    move.user_id = move_json.user_id
    move.battle_id = move_json.battle_id
    move.round = move_json.round
    move.choice = move_json.choice

    db_sess.add(move)
    db_sess.commit()
    move_json.id = move.id
    move_json.choice = move.choice.value

    # Check if the opponent has made a move
    for other_move in battle.moves:
        if other_move.round == move.round and other_move.user_id != move.user_id:

            # Game logic
            if other_move.choice == move.choice:
                print('noone')

            elif other_move.choice == Choice.rock:
                if move.choice == Choice.scissors:
                    pass # Other win
                else:
                    pass # Move win
            elif other_move.choice == Choice.paper:
                if move.choice == Choice.rock:
                    pass # Other win
                else:
                    pass # Move win
            elif other_move.choice == Choice.scissors:
                if move.choice == Choice.paper:
                    pass # Other win
                else:
                    pass # Move win
            break



    return move_json


if __name__ == "__main__":
    database.global_init_sqlite('db.sqlite')
    uvicorn.run(app, host="0.0.0.0", port=8000)
