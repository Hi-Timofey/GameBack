# -*- coding: utf-8 -*-
from pydantic_sqlalchemy import sqlalchemy_to_pydantic

# Importing models for out database
from .database import *

from .user import *
from .session_keys import *
from .accept import *
from .move import *
from .round import *
from .battle import *

PydanticAccept = sqlalchemy_to_pydantic(Accept)
PydanticBattle = sqlalchemy_to_pydantic(Battle)
