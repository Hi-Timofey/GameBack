from typing import List, Optional
from pydantic import BaseModel

class Accept(BaseModel):
    id: int
    acceptor: str
    offer_id: int

    class Config:
        orm_mode = True

class Offer(BaseModel):
    id: int
    creator: str
    accepts: List[Accept] = []

    class Config:
        orm_mode = True

class Blockchain(BaseModel):
    last_scanned_block: int

    class Config:
        orm_mode = True


