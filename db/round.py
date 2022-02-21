import sqlalchemy as sa
from sqlalchemy import orm

from .database import SqlAlchemyBase


class Round(SqlAlchemyBase):
    __tablename__ = 'rounds'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    round_number = sa.Column(sa.Integer)
    winner_user_address = sa.Column(sa.String(42), sa.ForeignKey("users.address"), nullable=True)
    winner_sid = sa.Column(sa.String, nullable=True)

    battle_id = sa.Column(sa.Integer, sa.ForeignKey("battles.id"))
    battle = orm.relationship("Battle")

    moves = orm.relationship("Move", back_populates='round')
