# -*- coding: utf-8 -*-
from pydantic_sqlalchemy import sqlalchemy_to_pydantic

# Importing models for out database
from .database import *  # noqa
from .user import *  # noqa
from .session_keys import *  # noqa
from .accept import *  # noqa
from .move import *  # noqa
from .round import *  # noqa
from .battle import *  # noqa

PydanticAccept = sqlalchemy_to_pydantic(Accept)  # noqa
PydanticBattle = sqlalchemy_to_pydantic(Battle)  # noqa
PydanticMove = sqlalchemy_to_pydantic(Move)  # noqa
PydanticRound = sqlalchemy_to_pydantic(Round)  # noqa
