import sqlalchemy as sa
from sqlalchemy import orm, Enum

from enum import IntEnum

from .database import SqlAlchemyBase


class Choice(IntEnum):
    attack = 1
    block = 2
    trick = 3


class Move(SqlAlchemyBase):
    __tablename__ = "moves"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    owner_address = sa.Column(sa.String(42), sa.ForeignKey("users.address"))

    round_id = sa.Column(sa.Integer, sa.ForeignKey("rounds.id"))
    round = orm.relationship("Round", back_populates="moves")

    choice = sa.Column(Enum(Choice))
