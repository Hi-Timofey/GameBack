from typing import List, Optional
from pydantic import BaseModel
from enum import IntEnum

class NFTType(IntEnum):
    shroom = 0
    bot = 1

class NFT(BaseModel):
    token_id: int
    nft_type: NFTType
    uri: Optional[str]

class NFTBalance(BaseModel):
    shrooms: List[NFT] = []
    bots: List[NFT] = []

class Accept(BaseModel):
    id: int
    acceptor: str
    nft: int
    nft_type: NFTType
    nft_uri: str
    bet: str
    offer_id: int

    class Config:
        orm_mode = True

class Offer(BaseModel):
    id: int
    creator: str
    nft: int
    nft_type: NFTType
    nft_uri: str
    bet: str
    accepts: List[Accept] = []

    class Config:
        orm_mode = True

class Blockchain(BaseModel):
    last_scanned_block: int

    class Config:
        orm_mode = True




