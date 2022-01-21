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
    id: int = None
    user_id: int
    nft_id: int
    offer_id: int

    class Config:
        orm_mode = True


class Offer(BaseModel):
    id: int = None
    user_id: int
    nft_id: int
    # nft_type: NFTType
    # nft_uri: str
    accepts: List[Accept] = []

    class Config:
        orm_mode = True


class Move(BaseModel):
    id: int = None
    user_id: int
    battle_id: int
    choice: int
    round: int


class Battle(BaseModel):
    id: int = None
    offer_id: int
    accept_id: int
    log: List[Move] = []
