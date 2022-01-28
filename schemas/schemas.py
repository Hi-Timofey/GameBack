from typing import List, Optional
from pydantic import BaseModel
from enum import IntEnum

from db.move import Choice


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
    round: int
    choice: Choice
    battle_id: int


class MoveCompact(BaseModel):
    user_id: int
    choice: Choice

    class Config:
        orm_mode = True

class Round(BaseModel):
    round_number: int
    battle_id: int
    winner_user_id: Optional[int]
    moves: List[MoveCompact] = []
    # winner_user_id: int

    class Config:
        orm_mode = True


class Battle(BaseModel):
    id: int = None
    offer_id: int
    accept_id: int
    log: List[Round] = []


class BattleId(BaseModel):
    battle_id: int

class LoginAddress(BaseModel):
    address: str

class LoginSigned(BaseModel):
    signed: str
