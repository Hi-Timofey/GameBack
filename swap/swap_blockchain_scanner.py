from web3 import Web3
from models import *
from database import SessionLocal, engine
import time
import traceback
import os

ORACLE_PRIVATE_KEY = os.environ['ORACLE_PRIVATE_KEY']
ORACLE_ADDRESS = os.environ['ORACLE_ADDRESS']

# RPC URLs
BSC_RPC_URL = 'https://bsc-dataseed.binance.org/'
POLYGON_RPC_URL = 'https://rpc-mainnet.matic.quiknode.pro'

# Contract addresses
QZQ_CONTRACT = '0x47b8E4661Ca02C258C362A9389f25Dae781C43f7'
BVC_ROUTER_CONTRACT = '0x7d0B9C5f772F03247DF9f914dEe955316d3853ED'

# Contract ABIs
QZQ_ABI = '''[
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "previousOwner",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "address",
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "OwnershipTransferred",
		"type": "event"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "renounceOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "transferOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]'''
BVC_ROUTER_ABI = '''[
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_BVCAddress",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "_swapOracle",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "_pancakeRouter",
				"type": "address"
			}
		],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "previousOwner",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "address",
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "OwnershipTransferred",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "swapId",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "address",
				"name": "swapper",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "amountReceived",
				"type": "uint256"
			}
		],
		"name": "QZQSwap",
		"type": "event"
	},
	{
		"inputs": [],
		"name": "BVCAddress",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "newOracle",
				"type": "address"
			}
		],
		"name": "changeOracle",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "swapId",
				"type": "uint256"
			}
		],
		"name": "claimSwap",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "swapId",
				"type": "uint256"
			},
			{
				"internalType": "address",
				"name": "swapper",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "amountSwapped",
				"type": "uint256"
			}
		],
		"name": "confirmSwap",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "pancakeRouter",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "renounceOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "swapOracle",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "amountSwapped",
				"type": "uint256"
			}
		],
		"name": "swapToQZQ",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "transferOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "withdrawBVC",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]'''

# Amount of blocks requested from RPC at once, more than 5000 is not allowed by the BSC node
BLOCK_CHUNK_SIZE = 5000

# Binding database models
Base.metadata.create_all(bind=engine)


'''
def get_abi(contract):
    return requests.get(f'https://api.polygonscan.com/api?module=contract&action=getabi&address={contract}').json()['result']
    return '[{"inputs":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"address","name":"nftTokenAddress","type":"address"},{"internalType":"address","name":"_beneficiary","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"},{"indexed":false,"internalType":"uint128","name":"acceptId","type":"uint128"},{"indexed":false,"internalType":"address","name":"acceptor","type":"address"},{"indexed":false,"internalType":"uint256","name":"nft","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"bet","type":"uint256"},{"indexed":false,"internalType":"enum GameContract.NFTType","name":"nfttype","type":"uint8"}],"name":"Accept","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"acceptId","type":"uint256"}],"name":"AcceptCancel","type":"event"},{"inputs":[{"internalType":"address","name":"offerCreator","type":"address"},{"internalType":"uint128","name":"offerId","type":"uint128"},{"internalType":"uint256","name":"nft","type":"uint256"},{"internalType":"enum GameContract.NFTType","name":"nfttype","type":"uint8"}],"name":"AcceptOffer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"anonymous":false,"inputs":[{"components":[{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog1","type":"tuple"},{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog2","type":"tuple"},{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog3","type":"tuple"},{"components":[{"internalType":"enum BattleContract.EArenaType","name":"_arena","type":"uint8"},{"components":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"botData","type":"tuple"},{"internalType":"int256","name":"Hp","type":"int256"},{"internalType":"uint256","name":"CritRound","type":"uint256"},{"internalType":"uint256","name":"BlockRound","type":"uint256"}],"internalType":"struct BattleContract.Bot","name":"_bot_1","type":"tuple"},{"components":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"botData","type":"tuple"},{"internalType":"int256","name":"Hp","type":"int256"},{"internalType":"uint256","name":"CritRound","type":"uint256"},{"internalType":"uint256","name":"BlockRound","type":"uint256"}],"internalType":"struct BattleContract.Bot","name":"_bot_2","type":"tuple"}],"internalType":"struct BattleContract.Battle","name":"battle","type":"tuple"}],"indexed":false,"internalType":"struct BattleContract.Log","name":"log","type":"tuple"},{"indexed":false,"internalType":"address","name":"creator","type":"address"},{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"}],"name":"BattleEnd","type":"event"},{"inputs":[{"internalType":"uint256","name":"offerId","type":"uint256"},{"internalType":"uint256","name":"acceptId","type":"uint256"}],"name":"CancelAccept","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"offerId","type":"uint256"}],"name":"CancelOffer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"nft","type":"uint256"},{"internalType":"enum GameContract.NFTType","name":"nfttype","type":"uint8"},{"internalType":"uint256","name":"bet","type":"uint256"}],"name":"CreateOffer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"creator","type":"address"},{"indexed":false,"internalType":"uint128","name":"offerId","type":"uint128"},{"indexed":false,"internalType":"uint256","name":"nft","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"bet","type":"uint256"},{"indexed":false,"internalType":"enum GameContract.NFTType","name":"nfttype","type":"uint8"}],"name":"Offer","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"creator","type":"address"},{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"}],"name":"OfferCancel","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_beneficiary","type":"address"}],"name":"setBeneficiary","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"name":"SetBotData","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"offerId","type":"uint256"},{"internalType":"uint256","name":"acceptId","type":"uint256"}],"name":"StartBattle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"_Test","outputs":[{"components":[{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog1","type":"tuple"},{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog2","type":"tuple"},{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog3","type":"tuple"},{"components":[{"internalType":"enum BattleContract.EArenaType","name":"_arena","type":"uint8"},{"components":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"botData","type":"tuple"},{"internalType":"int256","name":"Hp","type":"int256"},{"internalType":"uint256","name":"CritRound","type":"uint256"},{"internalType":"uint256","name":"BlockRound","type":"uint256"}],"internalType":"struct BattleContract.Bot","name":"_bot_1","type":"tuple"},{"components":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"botData","type":"tuple"},{"internalType":"int256","name":"Hp","type":"int256"},{"internalType":"uint256","name":"CritRound","type":"uint256"},{"internalType":"uint256","name":"BlockRound","type":"uint256"}],"internalType":"struct BattleContract.Bot","name":"_bot_2","type":"tuple"}],"internalType":"struct BattleContract.Battle","name":"battle","type":"tuple"}],"internalType":"struct BattleContract.Log","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"beneficiary","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"offerId","type":"uint256"}],"name":"GetAccepts","outputs":[{"components":[{"internalType":"uint128","name":"id","type":"uint128"},{"internalType":"uint128","name":"offerId","type":"uint128"},{"internalType":"address","name":"acceptor","type":"address"},{"internalType":"enum GameContract.NFTType","name":"nfttype","type":"uint8"},{"internalType":"uint256","name":"nft","type":"uint256"},{"internalType":"uint256","name":"bet","type":"uint256"}],"internalType":"struct GameContract.GameAccept[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_id","type":"uint256"}],"name":"GetBotData","outputs":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"}],"name":"GetOffers","outputs":[{"components":[{"internalType":"uint128","name":"id","type":"uint128"},{"internalType":"address","name":"creator","type":"address"},{"internalType":"enum GameContract.NFTType","name":"nfttype","type":"uint8"},{"internalType":"uint256","name":"nft","type":"uint256"},{"internalType":"uint256","name":"bet","type":"uint256"}],"internalType":"struct GameContract.GameOffer[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"nftAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]'
'''

def get_db():
    return SessionLocal()


def slice_list(S, step):
    if S is not None:
        return [S[x:x+step] for x in range(0, len(S),step)]
    else:
        return []


# Connecting to RPCs
bsc_w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
polygon_w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))

# Creating contract instances
qzq_contract = polygon_w3.eth.contract(address=QZQ_CONTRACT, abi=QZQ_ABI)
bvc_router_contract = bsc_w3.eth.contract(address=BVC_ROUTER_CONTRACT, abi=BVC_ROUTER_ABI)

while True:
    # Processing events on BSC
    try:
        # Get the latest BSC block
        last_bsc_block = bsc_w3.eth.block_number

        # Get the last scanned BSC block
        with get_db() as db:
            last_scanned_block = db.query(Blockchain).first().last_bsc_block

        if last_bsc_block == last_scanned_block:
            print('Fully synced up, sleeping...')
            time.sleep(0.75)
            continue

        # Make a block chunk
        # Checking if there are more than BLOCK_CHUNK_SIZE blocks to process
        if last_bsc_block - (last_scanned_block + 1) < BLOCK_CHUNK_SIZE:
            block_chunk = list(range(last_scanned_block + 1, last_bsc_block))
        else:
            block_chunk = list(range(last_scanned_block + 1, last_scanned_block + 1 + BLOCK_CHUNK_SIZE))

        # Processing the block chunk
        with get_db() as db:
            if len(block_chunk) < 2:
                print('Fully synced up, sleeping...')
                time.sleep(0.5)
                continue

            print(f'Processing events from block {block_chunk[0]} to {block_chunk[-1]}')

            # Processing QZQ -> BVC swap events on Polygon
            qzq_to_bvc_swaps = qzq_contract.events.BVCSwap.createFilter(
                fromBlock = block_chunk[0], toBlock = block_chunk[-1]
            ).get_all_entries()

            # Confirm swap on BSC
            for swap in qzq_to_bvc_swaps:
                nonce = bsc_w3.eth.get_transaction_count(ORACLE_ADDRESS)
                tx = bvc_router_contract.confirmSwap(
                    swap.args.swapId, swap.args.swapper, swap.args.amountSwapped
                ).build_transaction({
                    'nonce': nonce
                })
                signed_tx = bsc_w3.eth.account.sign_transaction(tx, private_key=ORACLE_PRIVATE_KEY)
                tx_hash = bsc_w3.eth.send_raw_transaction(signed_tx)
                print(f'Confirmed swap {tx_hash}')

            print(f'Processed {len(qzq_to_bvc_swaps)} QZQ -> BVC swaps.')

            # Update last scanned block
            last_scanned_block = db.query(Blockchain).first()
            last_scanned_block.last_bsc_block = block_chunk[-1]
            db.flush()
            db.commit()
    except Exception:
        traceback.print_exc()

    # Processing events on Polygon
    try:
        # Get the latest Polygon block
        last_polygon_block = polygon_w3.eth.block_number

        # Get the last scanned Polygon block
        with get_db() as db:
            last_scanned_block = db.query(Blockchain).first().last_polygon_block

        if last_polygon_block == last_scanned_block:
            print('Fully synced up, sleeping...')
            time.sleep(0.5)
            continue

        # Make a block chunk
        # Checking if there are more than BLOCK_CHUNK_SIZE blocks to process
        if last_bsc_block - (last_scanned_block + 1) < BLOCK_CHUNK_SIZE:
            block_chunk = list(range(last_scanned_block + 1, last_bsc_block))
        else:
            block_chunk = list(range(last_scanned_block + 1, last_scanned_block + 1 + BLOCK_CHUNK_SIZE))

        # Processing the block chunk
        with get_db() as db:
            if len(block_chunk) < 2:
                print('Fully synced up, sleeping...')
                time.sleep(0.75)
                continue

            print(f'Processing events from block {block_chunk[0]} to {block_chunk[-1]}')

            # Processing BVC -> QZQ swap events on BSC
            bvc_to_qzq_swaps = bvc_router_contract.events.QZQSwap.createFilter(
                fromBlock=block_chunk[0], toBlock=block_chunk[-1]
            ).get_all_entries()

            # Confirm swap on Polygon
            for swap in bvc_to_qzq_swaps:
                nonce = polygon_w3.eth.get_transaction_count(ORACLE_ADDRESS)
                tx = qzq_contract.confirmSwap(
                    swap.args.swapId, swap.args.swapper, swap.args.amountReceived
                ).build_transaction({
                    'nonce': nonce
                })
                signed_tx = polygon_w3.eth.account.sign_transaction(tx, private_key=ORACLE_PRIVATE_KEY)
                tx_hash = polygon_w3.eth.send_raw_transaction(signed_tx)
                print(f'Confirmed swap {tx_hash}')

            print(f'Processed {len(bvc_to_qzq_swaps)} BVC -> QZQ swaps.')

            # Update last scanned block
            last_scanned_block = db.query(Blockchain).first()
            last_scanned_block.last_polygon_block = block_chunk[-1]
            db.flush()
            db.commit()
    except Exception:
        traceback.print_exc()
