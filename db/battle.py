import sqlalchemy as sa
from typing import List
from sqlalchemy import orm, Enum
from enum import IntEnum
from .database import SqlAlchemyBase


class BattleState(IntEnum):
    listed = 1
    in_battle = 2
    ended = 3


class Battle(SqlAlchemyBase):
    __tablename__ = 'battles'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    nft_id = sa.Column(sa.Integer)

    accepts = orm.relationship("Accept", back_populates='battle')
    accepted_id = sa.Column(sa.Integer)

    log = orm.relationship("Round", back_populates='battle')
    battle_state = sa.Column(Enum(BattleState))
