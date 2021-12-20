from web3 import Web3
from models import *
from database import SessionLocal, engine
import time
import traceback

POLYGON_RPC_URL = 'https://rpc-mainnet.matic.quiknode.pro'
BATTLE_CONTRACT = '0x4f9037375791DE6B471596f6c99A374566Ec3c84'
BLOCK_CHUNK_SIZE = 2500

# Binding database models
Base.metadata.create_all(bind=engine)


def get_abi(contract):
    # return requests.get(f'https://api.polygonscan.com/api?module=contract&action=getabi&address={contract}').json()['result']
    return '[{"inputs":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"address","name":"nftTokenAddress","type":"address"},{"internalType":"address","name":"_beneficiary","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"acceptId","type":"uint256"},{"indexed":false,"internalType":"address","name":"acceptor","type":"address"},{"indexed":false,"internalType":"uint256","name":"nft","type":"uint256"}],"name":"Accept","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"acceptId","type":"uint256"}],"name":"AcceptCancel","type":"event"},{"inputs":[{"internalType":"address","name":"offerCreator","type":"address"},{"internalType":"uint128","name":"offerId","type":"uint128"},{"internalType":"uint256","name":"nft","type":"uint256"}],"name":"AcceptOffer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"anonymous":false,"inputs":[{"components":[{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog1","type":"tuple"},{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog2","type":"tuple"},{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog3","type":"tuple"},{"components":[{"internalType":"enum BattleContract.EArenaType","name":"_arena","type":"uint8"},{"components":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"botData","type":"tuple"},{"internalType":"int256","name":"Hp","type":"int256"},{"internalType":"uint256","name":"CritRound","type":"uint256"},{"internalType":"uint256","name":"BlockRound","type":"uint256"}],"internalType":"struct BattleContract.Bot","name":"_bot_1","type":"tuple"},{"components":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"botData","type":"tuple"},{"internalType":"int256","name":"Hp","type":"int256"},{"internalType":"uint256","name":"CritRound","type":"uint256"},{"internalType":"uint256","name":"BlockRound","type":"uint256"}],"internalType":"struct BattleContract.Bot","name":"_bot_2","type":"tuple"}],"internalType":"struct BattleContract.Battle","name":"battle","type":"tuple"}],"indexed":false,"internalType":"struct BattleContract.Log","name":"log","type":"tuple"},{"indexed":false,"internalType":"address","name":"creator","type":"address"},{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"}],"name":"BattleEnd","type":"event"},{"inputs":[{"internalType":"uint256","name":"offerId","type":"uint256"},{"internalType":"uint256","name":"acceptId","type":"uint256"}],"name":"CancelAccept","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"offerId","type":"uint256"}],"name":"CancelOffer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"nft","type":"uint256"},{"internalType":"uint256","name":"bet","type":"uint256"}],"name":"CreateOffer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"creator","type":"address"},{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"nft","type":"uint256"}],"name":"Offer","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"creator","type":"address"},{"indexed":false,"internalType":"uint256","name":"offerId","type":"uint256"}],"name":"OfferCancel","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_beneficiary","type":"address"}],"name":"setBeneficiary","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"name":"SetBotData","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"offerId","type":"uint256"},{"internalType":"uint256","name":"acceptId","type":"uint256"}],"name":"StartBattle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"_Test","outputs":[{"components":[{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog1","type":"tuple"},{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog2","type":"tuple"},{"components":[{"internalType":"uint256","name":"Id","type":"uint256"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_1","type":"tuple"},{"components":[{"internalType":"int256","name":"hpBefore","type":"int256"},{"internalType":"int256","name":"hpAfter","type":"int256"},{"internalType":"uint256","name":"attack","type":"uint256"},{"internalType":"uint256","name":"crit","type":"uint256"},{"internalType":"uint256","name":"_block","type":"uint256"},{"internalType":"uint256","name":"platform","type":"uint256"},{"internalType":"bool","name":"isCrit","type":"bool"}],"internalType":"struct BattleContract.RoundBot","name":"Bot_2","type":"tuple"}],"internalType":"struct BattleContract.Round","name":"_roundsLog3","type":"tuple"},{"components":[{"internalType":"enum BattleContract.EArenaType","name":"_arena","type":"uint8"},{"components":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"botData","type":"tuple"},{"internalType":"int256","name":"Hp","type":"int256"},{"internalType":"uint256","name":"CritRound","type":"uint256"},{"internalType":"uint256","name":"BlockRound","type":"uint256"}],"internalType":"struct BattleContract.Bot","name":"_bot_1","type":"tuple"},{"components":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"botData","type":"tuple"},{"internalType":"int256","name":"Hp","type":"int256"},{"internalType":"uint256","name":"CritRound","type":"uint256"},{"internalType":"uint256","name":"BlockRound","type":"uint256"}],"internalType":"struct BattleContract.Bot","name":"_bot_2","type":"tuple"}],"internalType":"struct BattleContract.Battle","name":"battle","type":"tuple"}],"internalType":"struct BattleContract.Log","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"beneficiary","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"offerId","type":"uint256"}],"name":"GetAccepts","outputs":[{"components":[{"internalType":"uint128","name":"id","type":"uint128"},{"internalType":"uint128","name":"offerId","type":"uint128"},{"internalType":"address","name":"acceptor","type":"address"},{"internalType":"uint256","name":"nft","type":"uint256"},{"internalType":"uint256","name":"bet","type":"uint256"}],"internalType":"struct GameContract.GameAccept[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_id","type":"uint256"}],"name":"GetBotData","outputs":[{"components":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"enum BattleContract.EWeaponType","name":"_weapon","type":"uint8"},{"internalType":"enum BattleContract.EToyType","name":"_toy","type":"uint8"},{"internalType":"enum BattleContract.EPlatformType","name":"_platform","type":"uint8"}],"internalType":"struct BattleContract.BotData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"}],"name":"GetOffers","outputs":[{"components":[{"internalType":"uint128","name":"id","type":"uint128"},{"internalType":"address","name":"creator","type":"address"},{"internalType":"uint256","name":"nft","type":"uint256"},{"internalType":"uint256","name":"bet","type":"uint256"}],"internalType":"struct GameContract.GameOffer[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"nftAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]'


def get_db():
    return SessionLocal()


def slice_list(S, step):
    if S is not None:
        return [S[x:x+step] for x in range(0, len(S),step)]
    else:
        return []


w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))
battle_contract = w3.eth.contract(address=BATTLE_CONTRACT, abi=get_abi(BATTLE_CONTRACT))

while True:
    try:
        # Get the latest block in a blockchain from Web3
        last_web3_block = w3.eth.block_number

        # Get the last scanned block
        with get_db() as db:
            last_scanned_block = db.query(Blockchain).first().last_scanned_block

        if last_web3_block == last_scanned_block:
            print('Fully synced up, sleeping...')
            time.sleep(0.75)
            continue

        # Make a block chunk
        if last_web3_block - (last_scanned_block + 1) < BLOCK_CHUNK_SIZE:
            block_chunk = list(range(last_scanned_block + 1, last_web3_block))
        else:
            block_chunk = list(range(last_scanned_block + 1, last_scanned_block + 1 + BLOCK_CHUNK_SIZE))

        # Processing the block chunk
        with get_db() as db:
            if not block_chunk:
                print('Fully synced up, sleeping...')
                time.sleep(0.75)
                continue
            if len(block_chunk) == 1:
                block_chunk.append(block_chunk[0])

            print(f'Processing events from block {block_chunk[0]} to {block_chunk[-1]}')

            # Processing offer creation events
            offer_events = battle_contract.events.Offer.createFilter(
                fromBlock = block_chunk[0], toBlock = block_chunk[-1]
            ).get_all_entries()

            new_offers = [Offer(id = event.args.offerId, creator = event.args.creator) for event in offer_events]
            db.bulk_save_objects(new_offers)
            db.flush()

            print(f'Processed {len(new_offers)} offer creations.')

            # Processing offer accept events
            accept_events = battle_contract.events.Accept.createFilter(
                fromBlock = block_chunk[0], toBlock = block_chunk[-1]
            ).get_all_entries()

            new_accepts = [
                Accept(id = event.args.acceptId,
                       acceptor = event.args.acceptor,
                       offer_id = event.args.offerId) for event in accept_events
            ]
            db.bulk_save_objects(new_accepts)
            db.flush()

            print(f'Processed {len(new_accepts)} offer accepts.')

            # Processing accept cancel events
            accept_cancel_events = battle_contract.events.AcceptCancel.createFilter(
                fromBlock=block_chunk[0], toBlock=block_chunk[-1]
            ).get_all_entries()

            for event in accept_cancel_events:
                cancelled_accept = Accept.query.filter(Accept.id == event.args.acceptId).first()
                db.delete(cancelled_accept)
            db.flush()

            print(f'Processed {len(accept_cancel_events)} cancelled accepts.')

            # Processing offer cancel events
            offer_cancel_events = battle_contract.events.OfferCancel.createFilter(
                fromBlock=block_chunk[0], toBlock=block_chunk[-1]
            ).get_all_entries()

            for event in offer_cancel_events:
                cancelled_offer = Offer.query.filter(Offer.id == event.args.offerId).first()
                db.delete(cancelled_offer)
            db.flush()

            print(f'Processed {len(offer_cancel_events)} offer removals.')

            # Update last scanned block
            last_scanned_block = db.query(Blockchain).first()
            last_scanned_block.last_scanned_block = block_chunk[-1]
            db.flush()
            db.commit()
    except Exception:
        traceback.print_exc()
