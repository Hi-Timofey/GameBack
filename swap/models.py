from sqlalchemy import Column, Integer
from database import Base

class Blockchain(Base):
    __tablename__ = "blockchain"

    id = Column(Integer, primary_key=True, index=True)
    last_bsc_block = Column(Integer)
    last_polygon_block = Column(Integer)
