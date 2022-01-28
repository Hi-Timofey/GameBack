import sqlalchemy as sa
from sqlalchemy import orm


from .database import SqlAlchemyBase


class Offer(SqlAlchemyBase):
    __tablename__ = 'offers'

    id = sa.Column(sa.Integer,primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id") )

    nft_id = sa.Column(sa.Integer)

    accepts = orm.relation("Accept", back_populates='offer')
