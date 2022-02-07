import sqlalchemy as sa
from sqlalchemy import orm

from pydantic_sqlalchemy import sqlalchemy_to_pydantic

from .database import SqlAlchemyBase


class Battle(SqlAlchemyBase):
    __tablename__ = 'battles'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    offer_id = sa.Column(sa.Integer, sa.ForeignKey("offers.id"))

    offer = orm.relationship("Offer")

    accept_id = sa.Column(sa.Integer, sa.ForeignKey("accepts.id"))
    accept = orm.relationship("Accept")

    # first_player_id = sa.Column(sa.Integer, sa.ForeignKey("offers.user_id"))
    # second_player_id = sa.Column(sa.Integer, sa.ForeignKey("accepts.user_id"))

    log =  orm.relationship("Round", back_populates='battle')

PydanticBattle = sqlalchemy_to_pydantic(Battle)

class PydanticBattles:
    battles: List[PydanticBattle]
