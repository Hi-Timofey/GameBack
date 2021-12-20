from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
import schemas
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from typing import List
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor

POLYGON_RPC = 'https://polygon-rpc.com/'
ETHEREUM_RPC = 'https://nodes.mewapi.io/rpc/eth'

SHROOMS_CONTRACT = '0xD558BF191abfe28CA37885605C7754E77F9DF0eF'
BOTS_CONTRACT = '0x0111546FEB693b9d9d5886e362472886b71D5337'

NFT_ABI = '[{ "constant": true, "inputs": [ { "name": "_owner", "type": "address" } ], "name": "balanceOf", "outputs": [ { "name": "balance", "type": "uint256" } ], "payable": false, "type": "function" }, { "constant": true, "inputs": [ { "name": "_owner", "type": "address" } ], "name": "walletOfOwner", "outputs": [ { "name": "balances", "type": "uint256[]" } ], "payable": false, "type": "function" }, { "constant": true, "inputs": [ { "name": "tokenId", "type": "uint256" } ], "name": "tokenURI", "outputs": [ { "name": "uri", "type": "string" } ], "payable": false, "type": "function"}]'

# Binding database models
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/battles/list', response_model = List[schemas.Offer])
def battles_list(request: Request, db: Session = Depends(get_db)):
    #if request.headers['host'] != 'api.battleverse.io':
    #    return HTTPException(404)
    return db.query(models.Offer).all()


@app.get('/battles/accepts', response_model = List[schemas.Offer])
def accepts_list(offer_id: int, request: Request, db: Session = Depends(get_db)):
    #if request.headers['host'] != 'api.battleverse.io':
    #    return HTTPException(404)
    return db.query(models.Accept).filter(models.Accept.offer_id == offer_id).all()


@app.get('/last_block', response_model = int)
def last_block(request: Request, db: Session = Depends(get_db)):
    #if request.headers['host'] != 'api.battleverse.io':
    #    return HTTPException(404)
    return db.query(models.Blockchain).first().last_scanned_block

@app.get('/nfts/{address}', response_model = schemas.NFTBalance)
def nfts_by_address(address: str, request: Request):
    #if request.headers['host'] != 'api.battleverse.io':
    #    return HTTPException(404)

    polygon = Web3(Web3.HTTPProvider(POLYGON_RPC))
    ethereum = Web3(Web3.HTTPProvider(ETHEREUM_RPC))

    shrooms = polygon.eth.contract(SHROOMS_CONTRACT, abi = NFT_ABI)
    bots = ethereum.eth.contract(BOTS_CONTRACT, abi=NFT_ABI)

    shroom_ids = shrooms.functions.walletOfOwner(address).call()
    bot_ids = bots.functions.walletOfOwner(address).call()

    def get_shroom(token_id):
        return schemas.NFT(token_id=token_id, uri=shrooms.functions.tokenURI(token_id).call())

    def get_bot(token_id):
        return schemas.NFT(token_id=token_id, uri=bots.functions.tokenURI(token_id).call())

    with ThreadPoolExecutor(max_workers=16) as executor:
        return schemas.NFTBalance(
            shrooms = list(
                executor.map(get_shroom, shroom_ids)
            ),
            bots = list(
                executor.map(get_bot, bot_ids)
            )
        )




