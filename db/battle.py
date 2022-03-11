import sqlalchemy as sa  # type: ignore
from sqlalchemy import orm, Enum
from sqlalchemy.ext.hybrid import hybrid_property  # type: ignore
from enum import IntEnum
from .database import SqlAlchemyBase
from .nft import NFTType

from web3 import Web3

POLYGON_RPC = "https://polygon-rpc.com/"
ETHEREUM_RPC = "https://nodes.mewapi.io/rpc/eth"

SHROOMS_CONTRACT = "0xD558BF191abfe28CA37885605C7754E77F9DF0eF"
BOTS_CONTRACT = "0x0111546FEB693b9d9d5886e362472886b71D5337"

NFT_ABI = (
    '[{ "constant": true, "inputs": [ { "name": "_owner", "type": "address" } ], "name": "balanceOf", '
    '"outputs": [ { "name": "balance", "type": "uint256" } ], "payable": false, "type": "function" }, '
    '{ "constant": true, "inputs": [ { "name": "_owner", "type": "address" } ], "name": "walletOfOwner", '
    '"outputs": [ { "name": "balances", "type": "uint256[]" } ], "payable": false, "type": "function" }, '
    '{ "constant": true, "inputs": [ { "name": "tokenId", "type": "uint256" } ], "name": "tokenURI", '
    '"outputs": [ { "name": "uri", "type": "string" } ], "payable": false, "type": "function"}] '
)


class BattleState(IntEnum):
    listed = 1
    in_battle = 2
    ended = 3


class Battle(SqlAlchemyBase):
    __tablename__ = "battles"
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    nft_id = sa.Column(sa.Integer)
    nft_type = sa.Column(Enum(NFTType))

    accepts = orm.relationship("Accept", back_populates="battle", cascade="all, delete")
    accepted_id = sa.Column(sa.Integer)

    bet = sa.Column(sa.String(80))

    log = orm.relationship("Round", back_populates="battle")
    battle_state = sa.Column(Enum(BattleState))

    owner_address = sa.Column(sa.String(42), sa.ForeignKey("users.address"))

    @hybrid_property
    def uri(self):
        polygon = Web3(Web3.HTTPProvider(POLYGON_RPC))
        ethereum = Web3(Web3.HTTPProvider(ETHEREUM_RPC))
        if self.nft_type == NFTType.bot:
            bots = ethereum.eth.contract(BOTS_CONTRACT, abi=NFT_ABI)
            bots_base_uri = bots.functions.tokenURI(0).call()[:-1]
            return bots_base_uri + str(self.nft_id)
        else:
            shrooms = polygon.eth.contract(SHROOMS_CONTRACT, abi=NFT_ABI)
            shrooms_base_uri = shrooms.functions.tokenURI(0).call()[:-1]
            return shrooms_base_uri + str(self.nft_id)
