from fastapi import FastAPI
from fastapi import HTTPException
import uvicorn
from typing import List
from sqlalchemy.orm import Session

import schemas

from db import database

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

    if db_sess.query(Battle).filter(Battle.offer_id == battle_json.offer_id).first():
        raise HTTPException(status_code=400, detail="Battle already started")

    battle = Battle()
    battle.offer_id = battle_json.offer_id
    battle.accept_id = battle_json.accept_id
    db_sess.add(battle)
    db_sess.commit()

    battle_json.id = battle.id

    return battle_json

if __name__ == "__main__":
    database.global_init_sqlite('db.sqlite')
    uvicorn.run(app, host="0.0.0.0", port=8000)
