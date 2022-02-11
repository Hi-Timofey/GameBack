import sqlalchemy as sa
from typing import List
from sqlalchemy import orm, Enum
from .database import SqlAlchemyBase
from .chains import Chain
from .nft import NFTType

class Accept(SqlAlchemyBase):
    __tablename__ = 'accepts'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)


    nft_id = sa.Column(sa.Integer)
    nft_type = sa.Column(Enum(NFTType))

    battle_id = sa.Column(sa.Integer, sa.ForeignKey("battles.id"))
    battle = orm.relationship("Battle", back_populates='accepts')
