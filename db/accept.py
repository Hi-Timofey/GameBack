import sqlalchemy as sa
from sqlalchemy import orm

from .database import SqlAlchemyBase


class Accept(SqlAlchemyBase):
    __tablename__ = 'accepts'

    id = sa.Column(sa.Integer,primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    nft_id = sa.Column(sa.Integer)

    offer_id = sa.Column(sa.Integer, sa.ForeignKey("offers.id"))
    offer = orm.relationship("Offer", back_populates="accepts")
