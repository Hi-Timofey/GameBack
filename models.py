from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    creator = Column(String(42), index=True)
    nft = Column(Integer, index=True)
    nft_type = Column(Integer, index=True)
    nft_uri = Column(String(255), index=True)
    bet = Column(String(78))
    accepts = relationship("Accept", back_populates="offer")


class Accept(Base):
    __tablename__ = "accepts"

    id = Column(Integer, primary_key=True, index=True)
    acceptor = Column(String(42), index=True)
    nft = Column(Integer, index=True)
    nft_type = Column(Integer, index=True)
    nft_uri = Column(String(255), index=True)
    bet = Column(String(78))
    offer_id = Column(Integer, ForeignKey("offers.id"))

    offer = relationship("Offer", back_populates="accepts")


class Blockchain(Base):
    __tablename__ = "blockchain"

    id = Column(Integer, primary_key=True, index=True)
    last_scanned_block = Column(Integer)
