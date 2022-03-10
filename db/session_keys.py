import sqlalchemy as sa
import datetime

from .database import SqlAlchemyBase


class SessionKey(SqlAlchemyBase):
    __tablename__ = 'session_keys'

    session_key = sa.Column(sa.String, primary_key=True, unique=True)
    user_address = sa.Column(sa.String)

    verified = sa.Column(sa.Boolean, default=False)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
