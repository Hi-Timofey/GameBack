import sqlalchemy as sa
from sqlalchemy import orm, Enum

from enum import IntEnum

from .database import SqlAlchemyBase


class Choice(IntEnum):
    rock = 1
    paper = 2
    scissors = 3


class Move(SqlAlchemyBase):
    __tablename__ = 'moves'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))

    round_id = sa.Column(sa.Integer, sa.ForeignKey("rounds.id"))
    round = orm.relationship("Round", back_populates="moves")

    choice = sa.Column(Enum(Choice))
