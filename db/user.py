import sqlalchemy as sa
from sqlalchemy import orm

from .database import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    address = Column(String(42), index=True)
