from typing import List, Optional
from pydantic import BaseModel

class Accept(BaseModel):
    id: int
    acceptor: str
    nft: int
    offer_id: int

    class Config:
        orm_mode = True

class Offer(BaseModel):
    id: int
    creator: str
    nft: int
    accepts: List[Accept] = []

    class Config:
        orm_mode = True

class Blockchain(BaseModel):
    last_scanned_block: int

    class Config:
        orm_mode = True

class NFT(BaseModel):
    token_id: int
    uri: str

class NFTBalance(BaseModel):
    shrooms: List[NFT] = []
    bots: List[NFT] = []


