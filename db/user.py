import sqlalchemy as sa

from .database import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    address = sa.Column(sa.String(42), index=True, primary_key=True)
