from fastapi import FastAPI, Depends, Request, HTTPException
import models
import schemas
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from typing import List

# Binding database models
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/battles/list', response_model = List[schemas.Offer])
def battles_list(request: Request, db: Session = Depends(get_db)):
    if request.headers['host'] != 'api.battleverse.io':
        return HTTPException(404)
    return db.query(models.Offer).all()


@app.get('/battles/accepts', response_model = List[schemas.Offer])
def accepts_list(offer_id: int, request: Request, db: Session = Depends(get_db)):
    if request.headers['host'] != 'api.battleverse.io':
        return HTTPException(404)
    return db.query(models.Accept).filter(models.Accept.offer_id == offer_id).all()


@app.get('/last_block', response_model = int)
def last_block(request: Request, db: Session = Depends(get_db)):
    if request.headers['host'] != 'api.battleverse.io':
        return HTTPException(404)
    return db.query(models.Blockchain).first().last_scanned_block


