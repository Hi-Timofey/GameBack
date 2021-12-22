from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
import schemas
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from typing import List, Optional
from web3 import Web3
import random

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


def get_nft_base_uris():
    polygon = Web3(Web3.HTTPProvider(POLYGON_RPC))
    ethereum = Web3(Web3.HTTPProvider(ETHEREUM_RPC))

    shrooms = polygon.eth.contract(SHROOMS_CONTRACT, abi=NFT_ABI)
    bots = ethereum.eth.contract(BOTS_CONTRACT, abi=NFT_ABI)

    shrooms_base_uri = shrooms.functions.tokenURI(0)[:-1]
    bots_base_uri = bots.functions.tokenURI(0)[:-1]

    return shrooms_base_uri, bots_base_uri

@app.get('/battles/list', response_model = List[schemas.Offer])
def battles_list(request: Request, address: Optional[str] = None, db: Session = Depends(get_db)):
    #if request.headers['host'] != 'api.battleverse.io':
    #    return HTTPException(404)

    if address:
        return db.query(models.Offer).filter(models.Offer.creator == address).all()
    else:
        return db.query(models.Offer).all()

@app.get('/battles/recommended', response_model = List[schemas.Offer])
def battles_recommended(request: Request, db: Session = Depends(get_db)):
    #if request.headers['host'] != 'api.battleverse.io':
    #    return HTTPException(404)
    all_offers = db.query(models.Offer).all()
    if len(all_offers) >= 3:
        return random.sample(all_offers, k=3)
    else:
        return all_offers



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

    address = Web3.toChecksumAddress(address)

    polygon = Web3(Web3.HTTPProvider(POLYGON_RPC))
    ethereum = Web3(Web3.HTTPProvider(ETHEREUM_RPC))

    shrooms = polygon.eth.contract(SHROOMS_CONTRACT, abi = NFT_ABI)
    bots = ethereum.eth.contract(BOTS_CONTRACT, abi=NFT_ABI)

    shroom_ids = shrooms.functions.walletOfOwner(address).call()
    bot_ids = bots.functions.walletOfOwner(address).call()

    shrooms_base_uri, bots_base_uri = get_nft_base_uris()

    return schemas.NFTBalance(
        shrooms = [
            schemas.NFT(
                token_id=token_id,
                nft_type=schemas.NFTType.shroom,
                uri=shrooms_base_uri + str(token_id))
            for token_id in shroom_ids
        ],
        bots=[
            schemas.NFT(
                token_id=token_id,
                nft_type=schemas.NFTType.bot,
                uri=bots_base_uri + str(token_id))
            for token_id in bot_ids
        ]
    )




