from fastapi import FastAPI
from fastapi import Response, status, HTTPException, Cookie
import uvicorn
from typing import List, Union, Optional
from sqlalchemy.orm import Session
import web3
from eth_account.messages import encode_defunct

import uuid
import random

import schemas

from db import database

from db.session_keys import SessionKey
from db.round import Round
from db.move import Move, Choice
from db.accept import Accept
from db.offer import Offer
from db.battle import Battle


app = FastAPI()


def check_session(db: Session, session_key: str) -> bool:
    try:
        session_key = db.query(SessionKey).filter(
            SessionKey.session_key == session_key).first()
        return session_key.verified
    except BaseException:
        return False


@app.get("/")
async def index():
    return 'Hello, im working'


@app.post("/login")
async def index(response: Response, json: schemas.LoginAddress, session_key: Optional[str] = Cookie(None)):
    db_sess = database.create_session()
    address = json.address
    random_string = uuid.uuid4()

    session_key = SessionKey(
        session_key=str(random_string),
        user_address=address,
    )

    db_sess.add(session_key)
    db_sess.commit()

    response.status_code = status.HTTP_201_CREATED
    response.set_cookie(key="session_key", value=random_string)
    return {'session_key': random_string}


@app.post("/signature")
async def index(response: Response, json: schemas.LoginSigned, session_key: Optional[str] = Cookie(None)):
    db_sess = database.create_session()
    w3 = web3.Web3()
    signature = json.signed
    account_recovered = w3.eth.account.recover_message(
        encode_defunct(text=session_key), signature=signature)


    session = db_sess.query(SessionKey).filter(
        SessionKey.session_key == session_key).first()

    if session.user_address == account_recovered:
        session.verified = True
        db_sess.add(session)
        db_sess.commit()
        response.status_code = status.HTTP_200_OK
        return {"session_key": session_key, "verified": True}
    else:
        raise HTTPException(status_code=400, detail="Session not verified")


@app.post("/battles/create", response_model=schemas.Offer)
async def create_offers(offer_json: schemas.Offer, response: Response, session_key: str = Cookie(None)):

    db_sess = database.create_session()
    if not check_session(db_sess, session_key):
        raise HTTPException(status_code=401)

    offer_db = Offer()

    offer_db.user_id = offer_json.user_id
    offer_db.nft_id = offer_json.nft_id

    db_sess.add(offer_db)
    db_sess.commit()

    offer_json.id = offer_db.id

    response.status_code = status.HTTP_201_CREATED
    return offer_json


@app.get("/battles/list", response_model=List[schemas.Offer])
async def list_offers(  user_id: Optional[int] = None, session_key: str = Cookie(None)):
    db_sess = database.create_session()

    if not check_session(db_sess, session_key):
        raise HTTPException(status_code=401)

    if user_id:
        offers = db_sess.query(Offer).filter(Offer.user_id == user_id).all()
    else:
        offers = db_sess.query(Offer).all()

    return offers

@app.get("/battles/recommended", response_model=List[schemas.Offer])
async def list_offers(session_key: str = Cookie(None)):
    db_sess = database.create_session()

    if not check_session(db_sess, session_key):
        raise HTTPException(status_code=401)


    all_offers = db_sess.query(Offer).all()
