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

    id = sa.Column(sa.Integer,primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.Integer)

    battle_id = sa.Column(sa.Integer, sa.ForeignKey("battles.id"))
    battle = orm.relationship("Battle")

    # TODO: Enum it
    choice = sa.Column(Enum(Choice))

    round = sa.Column(sa.Integer)


