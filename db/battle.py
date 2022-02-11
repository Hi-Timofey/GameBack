import sqlalchemy as sa
from typing import List
from sqlalchemy import orm, Enum
from enum import IntEnum
from .database import SqlAlchemyBase
from .chains import Chain
from .nft import NFTType


class BattleState(IntEnum):
    listed = 1
    in_battle = 2
    ended = 3


class Battle(SqlAlchemyBase):
    __tablename__ = 'battles'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    nft_id = sa.Column(sa.Integer)
    nft_type = sa.Column(Enum(NFTType))

    accepts = orm.relationship("Accept", back_populates='battle')
    accepted_id = sa.Column(sa.Integer)

    bet = sa.Column(sa.String(80))

    log = orm.relationship("Round", back_populates='battle')
    battle_state = sa.Column(Enum(BattleState))
