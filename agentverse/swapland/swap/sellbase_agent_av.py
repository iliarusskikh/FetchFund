#agent1qwpv6dygtaq2ptdnmdd3mzqnsh38pmecxsddkc4lsy9sx7kea2t82dfv6g2 mailbox address

from uuid import uuid4
from uagents import Agent, Protocol, Context, Model, Field
from uagents.experimental.quota import QuotaProtocol, RateLimit

import os
import logging
import sys
import requests
import atexit
from dotenv import load_dotenv
import json
from typing import Optional
from datetime import datetime, timedelta
from typing import Any
import decimal
from decimal import Decimal

#uniswap libraries
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec, V4Constants
from web3 import Account, Web3


load_dotenv()
SELLBASE_SEED = os.getenv("SELLBASE_SEED")

USERINPUT_AGENT="agent1q2aczah05l97w8mnen2lcc59y052w8mphzwgv0q37npm9fml2fz5sw2s4vz"
chain_id = 8453
rpc_endpoint = "https://mainnet.base.org"


# Configure Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Log on exit
def log_and_exit():
    logging.debug("🚨 Script terminated unexpectedly")
atexit.register(log_and_exit)

# Catch unexpected errors
def handle_unexpected_exception(exc_type, exc_value, exc_traceback):
    logging.error("🔥 Uncaught Exception:", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_unexpected_exception


class SwaplandRequest(Model):
    blockchain: str = Field(
        description="Blockchain name",
    )
    signal: str = Field(
        description="Buy or Sell signal",
    )
    amount: float = Field(
        description="Amount to be swapped",
    )
    private_key: str = Field(
        description="User's EVM private key",
    )
    
    
class SwaplandResponse(Model):
    status: str = Field(
        description="Status response from Swapland Agent",
    )

class SwapCompleted(Model):
    status: str= Field(
        description="Status response from Swapland Agent",
    )
    message: str = Field(
        description="Additional information",
    )
    transaction : str = Field(
        description="Transaction info",
    )
    

# Initialize Agent
agent2 = Agent(
    name="FetchFund - Sell signal on base agent",
    port=8020,
    seed=SELLBASE_SEED,
    mailbox = True,
    #readme_path = "README_sellbase.md",
    )


@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")





@agent2.on_message(model=SwaplandRequest)
async def handle_message(ctx: Context, sender: str, msg: SwaplandRequest):
    """Handle incoming messages"""
    global agent_response
    try:
        amount_to_swap = msg.amount
        private_key = msg.private_key
        signal = msg.signal
        network = msg.blockchain
        
        logger.info(f"Processed response: {msg}")
        
        rpl = "Swapping in progress.."
        rp = SwaplandResponse(status = rpl)
        await ctx.send(USERINPUT_AGENT,rp)
        
        try:
            await execute_swap(ctx, sender, msg) #do the swap
        except Exception as e:
            rpl = f"Error sending data to agent: {e}"
            logger.error(rpl)
            rp = SwaplandResponse(status = rpl)
            await ctx.send(USERINPUT_AGENT,rp)
        
        logger.info(f"Called function execute_swap")
        #return jsonify({"status": "success"})

    except Exception as e:
        rpl = f"Error in webhook: {e}"
        logger.error(rpl)
        rp = SwaplandResponse(status = rpl)
        await ctx.send(USERINPUT_AGENT,rp)
        return jsonify({"error": str(e)}), 500





async def execute_swap(ctx: Context, sender: str, msg: SwaplandRequest):
    try:
        uni_address = Web3.to_checksum_address('0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913')
        uni_abi = '[{"inputs":[{"internalType":"address","name":"implementationContract","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"previousAdmin","type":"address"},{"indexed":false,"internalType":"address","name":"newAdmin","type":"address"}],"name":"AdminChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"implementation","type":"address"}],"name":"Upgraded","type":"event"},{"stateMutability":"payable","type":"fallback"},{"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newAdmin","type":"address"}],"name":"changeAdmin","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"implementation","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newImplementation","type":"address"}],"name":"upgradeTo","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newImplementation","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"upgradeToAndCall","outputs":[],"stateMutability":"payable","type":"function"}]'

        #amount_in = int(0.0001 * 10**18)#18  working with 4
        amount_in = int(msg.amount * 10**18)
        min_amount_out = 1 * 10**4 #10**6 == 1USDC  working with 5

        weth_address = Web3.to_checksum_address('0x4200000000000000000000000000000000000006')

        path = [weth_address, uni_address]

        #uniswap router smart contract
        ur_address = Web3.to_checksum_address("0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD")
        ur_abi = '[{"inputs":[{"components":[{"internalType":"address","name":"permit2","type":"address"},{"internalType":"address","name":"weth9","type":"address"},{"internalType":"address","name":"seaportV1_5","type":"address"},{"internalType":"address","name":"seaportV1_4","type":"address"},{"internalType":"address","name":"openseaConduit","type":"address"},{"internalType":"address","name":"nftxZap","type":"address"},{"internalType":"address","name":"x2y2","type":"address"},{"internalType":"address","name":"foundation","type":"address"},{"internalType":"address","name":"sudoswap","type":"address"},{"internalType":"address","name":"elementMarket","type":"address"},{"internalType":"address","name":"nft20Zap","type":"address"},{"internalType":"address","name":"cryptopunks","type":"address"},{"internalType":"address","name":"looksRareV2","type":"address"},{"internalType":"address","name":"routerRewardsDistributor","type":"address"},{"internalType":"address","name":"looksRareRewardsDistributor","type":"address"},{"internalType":"address","name":"looksRareToken","type":"address"},{"internalType":"address","name":"v2Factory","type":"address"},{"internalType":"address","name":"v3Factory","type":"address"},{"internalType":"bytes32","name":"pairInitCodeHash","type":"bytes32"},{"internalType":"bytes32","name":"poolInitCodeHash","type":"bytes32"}],"internalType":"struct RouterParameters","name":"params","type":"tuple"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"BalanceTooLow","type":"error"},{"inputs":[],"name":"BuyPunkFailed","type":"error"},{"inputs":[],"name":"ContractLocked","type":"error"},{"inputs":[],"name":"ETHNotAccepted","type":"error"},{"inputs":[{"internalType":"uint256","name":"commandIndex","type":"uint256"},{"internalType":"bytes","name":"message","type":"bytes"}],"name":"ExecutionFailed","type":"error"},{"inputs":[],"name":"FromAddressIsNotOwner","type":"error"},{"inputs":[],"name":"InsufficientETH","type":"error"},{"inputs":[],"name":"InsufficientToken","type":"error"},{"inputs":[],"name":"InvalidBips","type":"error"},{"inputs":[{"internalType":"uint256","name":"commandType","type":"uint256"}],"name":"InvalidCommandType","type":"error"},{"inputs":[],"name":"InvalidOwnerERC1155","type":"error"},{"inputs":[],"name":"InvalidOwnerERC721","type":"error"},{"inputs":[],"name":"InvalidPath","type":"error"},{"inputs":[],"name":"InvalidReserves","type":"error"},{"inputs":[],"name":"InvalidSpender","type":"error"},{"inputs":[],"name":"LengthMismatch","type":"error"},{"inputs":[],"name":"SliceOutOfBounds","type":"error"},{"inputs":[],"name":"TransactionDeadlinePassed","type":"error"},{"inputs":[],"name":"UnableToClaim","type":"error"},{"inputs":[],"name":"UnsafeCast","type":"error"},{"inputs":[],"name":"V2InvalidPath","type":"error"},{"inputs":[],"name":"V2TooLittleReceived","type":"error"},{"inputs":[],"name":"V2TooMuchRequested","type":"error"},{"inputs":[],"name":"V3InvalidAmountOut","type":"error"},{"inputs":[],"name":"V3InvalidCaller","type":"error"},{"inputs":[],"name":"V3InvalidSwap","type":"error"},{"inputs":[],"name":"V3TooLittleReceived","type":"error"},{"inputs":[],"name":"V3TooMuchRequested","type":"error"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"RewardsSent","type":"event"},{"inputs":[{"internalType":"bytes","name":"looksRareClaim","type":"bytes"}],"name":"collectRewards","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes","name":"commands","type":"bytes"},{"internalType":"bytes[]","name":"inputs","type":"bytes[]"}],"name":"execute","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes","name":"commands","type":"bytes"},{"internalType":"bytes[]","name":"inputs","type":"bytes[]"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"execute","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint256[]","name":"","type":"uint256[]"},{"internalType":"uint256[]","name":"","type":"uint256[]"},{"internalType":"bytes","name":"","type":"bytes"}],"name":"onERC1155BatchReceived","outputs":[{"internalType":"bytes4","name":"","type":"bytes4"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bytes","name":"","type":"bytes"}],"name":"onERC1155Received","outputs":[{"internalType":"bytes4","name":"","type":"bytes4"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bytes","name":"","type":"bytes"}],"name":"onERC721Received","outputs":[{"internalType":"bytes4","name":"","type":"bytes4"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"int256","name":"amount0Delta","type":"int256"},{"internalType":"int256","name":"amount1Delta","type":"int256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"uniswapV3SwapCallback","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'


        codec = RouterCodec()

        encoded_input = (
                codec
                .encode
                .chain()
                .wrap_eth(FunctionRecipient.ROUTER, amount_in)
                .v2_swap_exact_in(FunctionRecipient.SENDER, amount_in, min_amount_out, path, payer_is_sender=False)
                .build(codec.get_default_deadline())
        )

        w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
        
        # For demo/test purposes, we'll simulate success without using actual private keys
        #if not privatekey or privatekey == "0x0000000000000000000000000000000000000000000000000000000000000000":
        #    logger.info("Using demo mode with simulated transaction")
        #    trx_hash = "0x" + "0" * 64  # Fake transaction hash
        #    logger.info(f"Simulated Trx Hash: {trx_hash}")
        #    logger.info(f"Simulated successful conversion from ETH to USDC.")
        #    send_status()  # Send success status to main agent
        #    return
            
        account = Account.from_key(msg.private_key)

        trx_params = {
                "from": account.address,
                "to": ur_address,
                "gas": 500_000, #make sure sufficient gas
                "maxPriorityFeePerGas": w3.eth.max_priority_fee,
                "maxFeePerGas": w3.eth.gas_price * 2,
                "type": '0x2',
                "chainId": chain_id,
                "value": amount_in,
                "nonce": w3.eth.get_transaction_count(account.address),
                "data": encoded_input,
        }

        raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).rawTransaction
        trx_hash = w3.eth.send_raw_transaction(raw_transaction)
        logger.info(f"Trx Hash: {w3.to_hex(trx_hash)}")
        logger.info(f"Successfully converted from ETH to USDC.")
        
        trxhash = "basescan.org/tx/"+str(w3.to_hex(trx_hash))
        
        rp = SwapCompleted(status = "success", message = "Successfully swapped ETH to USDC.", transaction = trxhash)
        await ctx.send(USERINPUT_AGENT,rp)
        
    except Exception as e:
        ero=f"Error in execute_swap: {e}"
        logger.error(ero)
        # Still send successful status to keep the flow going
        trxhash="None"
        rp = SwapCompleted(status = "fail", message = ero , transaction = trxhash)
        await ctx.send(USERINPUT_AGENT,rp)



if __name__ == '__main__':
    agent2.run()
