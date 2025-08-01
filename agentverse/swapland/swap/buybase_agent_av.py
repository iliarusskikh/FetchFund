#agent1qfjda5fqgu3qwvcww8z3jwwnsf9rhq0x09y27f0z2lkphszjl4gcwdp8h5u mailbox address

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
BUYBASE_SEED = os.getenv("BUYBASE_SEED")

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
    name="FetchFund - Buy signal on base agent",
    port=8019,
    seed=BUYBASE_SEED,
    mailbox = True,
    #readme_path = "README_buybase.md",
    )


@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
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
    # USDC contract for approval
    usdc_abi = '[{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"address","name":"minter_","type":"address"},{"internalType":"uint256","name":"mintingAllowedAfter_","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"delegator","type":"address"},{"indexed":true,"internalType":"address","name":"fromDelegate","type":"address"},{"indexed":true,"internalType":"address","name":"toDelegate","type":"address"}],"name":"DelegateChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"delegate","type":"address"},{"indexed":false,"internalType":"uint256","name":"previousBalance","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"newBalance","type":"uint256"}],"name":"DelegateVotesChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"minter","type":"address"},{"indexed":false,"internalType":"address","name":"newMinter","type":"address"}],"name":"MinterChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DELEGATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"DOMAIN_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"rawAmount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint32","name":"","type":"uint32"}],"name":"checkpoints","outputs":[{"internalType":"uint32","name":"fromBlock","type":"uint32"},{"internalType":"uint96","name":"votes","type":"uint96"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"delegatee","type":"address"}],"name":"delegate","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"delegatee","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"delegateBySig","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"delegates","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"getCurrentVotes","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"uint256","name":"blockNumber","type":"uint256"}],"name":"getPriorVotes","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"minimumTimeBetweenMints","outputs":[{"internalType":"uint32","name":"","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"rawAmount","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"mintCap","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"minter","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"mintingAllowedAfter","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"numCheckpoints","outputs":[{"internalType":"uint32","name":"","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"rawAmount","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"minter_","type":"address"}],"name":"setMinter","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"rawAmount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"rawAmount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"}]'

    # permit2 nonce, allowance and expiration
    permit2_abi = '[{"inputs":[{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"AllowanceExpired","type":"error"},{"inputs":[],"name":"ExcessiveInvalidation","type":"error"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"InsufficientAllowance","type":"error"},{"inputs":[{"internalType":"uint256","name":"maxAmount","type":"uint256"}],"name":"InvalidAmount","type":"error"},{"inputs":[],"name":"InvalidContractSignature","type":"error"},{"inputs":[],"name":"InvalidNonce","type":"error"},{"inputs":[],"name":"InvalidSignature","type":"error"},{"inputs":[],"name":"InvalidSignatureLength","type":"error"},{"inputs":[],"name":"InvalidSigner","type":"error"},{"inputs":[],"name":"LengthMismatch","type":"error"},{"inputs":[{"internalType":"uint256","name":"signatureDeadline","type":"uint256"}],"name":"SignatureExpired","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint160","name":"amount","type":"uint160"},{"indexed":false,"internalType":"uint48","name":"expiration","type":"uint48"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"address","name":"spender","type":"address"}],"name":"Lockdown","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint48","name":"newNonce","type":"uint48"},{"indexed":false,"internalType":"uint48","name":"oldNonce","type":"uint48"}],"name":"NonceInvalidation","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint160","name":"amount","type":"uint160"},{"indexed":false,"internalType":"uint48","name":"expiration","type":"uint48"},{"indexed":false,"internalType":"uint48","name":"nonce","type":"uint48"}],"name":"Permit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"word","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"mask","type":"uint256"}],"name":"UnorderedNonceInvalidation","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint48","name":"newNonce","type":"uint48"}],"name":"invalidateNonces","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"wordPos","type":"uint256"},{"internalType":"uint256","name":"mask","type":"uint256"}],"name":"invalidateUnorderedNonces","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"internalType":"struct IAllowanceTransfer.TokenSpenderPair[]","name":"approvals","type":"tuple[]"}],"name":"lockdown","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"nonceBitmap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails[]","name":"details","type":"tuple[]"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitBatch","name":"permitBatch","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails","name":"details","type":"tuple"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitSingle","name":"permitSingle","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions","name":"permitted","type":"tuple"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails","name":"transferDetails","type":"tuple"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions[]","name":"permitted","type":"tuple[]"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitBatchTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails[]","name":"transferDetails","type":"tuple[]"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions","name":"permitted","type":"tuple"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails","name":"transferDetails","type":"tuple"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes32","name":"witness","type":"bytes32"},{"internalType":"string","name":"witnessTypeString","type":"string"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitWitnessTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions[]","name":"permitted","type":"tuple[]"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitBatchTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails[]","name":"transferDetails","type":"tuple[]"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes32","name":"witness","type":"bytes32"},{"internalType":"string","name":"witnessTypeString","type":"string"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitWitnessTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"address","name":"token","type":"address"}],"internalType":"struct IAllowanceTransfer.AllowanceTransferDetails[]","name":"transferDetails","type":"tuple[]"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"address","name":"token","type":"address"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"}]'  # noqa


    #private_key = os.getenv("METAMASK_PRIVATE_KEY")
    #if not private_key:
    #    raise ValueError("METAMASK_PRIVATE_KEY not set")

    chain_id = 8453  # Base network
    rpc_endpoint = "https://mainnet.base.org"

    w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
    account = Account.from_key(msg.private_key)

    # Token addresses
    usdc_address = Web3.to_checksum_address('0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913')  # USDC
    weth_address = Web3.to_checksum_address('0x4200000000000000000000000000000000000006')  # WETH
    ur_address = Web3.to_checksum_address("0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD")  # Universal Router
    permit2_address = Web3.to_checksum_address("0x000000000022D473030F116dDEE9F6B43aC78BA3")

    usdc_contract = w3.eth.contract(address=usdc_address, abi=usdc_abi)
    #usdc_balance = usdc_contract.functions.balanceOf(account.address).call()


    # Check and approve Permit2
    permit2_allowance_needed = 2**256 - 1
    current_allowance = usdc_contract.functions.allowance(account.address, permit2_address).call()
    nonce = w3.eth.get_transaction_count(account.address, 'pending')

    if current_allowance < permit2_allowance_needed:
        approve_permit2_tx = usdc_contract.functions.approve(permit2_address, permit2_allowance_needed).build_transaction({
            "from": account.address,
            "gas": 100_000,
            "maxPriorityFeePerGas": w3.eth.max_priority_fee * 2,
            "maxFeePerGas": w3.eth.gas_price * 3,
            "nonce": nonce,
            "chainId": chain_id,
            "value": 0,
        })
        signed_permit2_tx = w3.eth.account.sign_transaction(approve_permit2_tx, msg.private_key)
        try:
            permit2_tx_hash = w3.eth.send_raw_transaction(signed_permit2_tx.rawTransaction)
            print(f"Permit2 Approve Tx Hash: {w3.to_hex(permit2_tx_hash)}")
            w3.eth.wait_for_transaction_receipt(permit2_tx_hash, timeout=120)  # 2 min timeout
        except ValueError as e:
            if 'replacement transaction underpriced' in str(e):
                print("Pending Permit2 approval detected; increase gas or wait...")
                raise e
            elif 'already known' in str(e):
                print("Permit2 approval already submitted; skipping...")
            else:
                raise e
    else:
        print("Permit2 already approved; skipping approval.")
    print("Permit2 UNI allowance:", current_allowance)

    #permit2 allowance check
    permit2_contract = w3.eth.contract(address=permit2_address, abi=permit2_abi)
    p2_amount, p2_expiration, p2_nonce = permit2_contract.functions.allowance(account.address,usdc_address,ur_address).call()
    print(
            "p2_amount, p2_expiration, p2_nonce: ",
            p2_amount,
            p2_expiration,
            p2_nonce,
    )


    codec = RouterCodec()

    # permit message
    allowance_amount = 2**160 - 1  # max/infinite
    permit_data, signable_message = codec.create_permit2_signable_message(
            usdc_address,
            allowance_amount,
            codec.get_default_expiration(),  # 30 days
            p2_nonce,
            ur_address,
            codec.get_default_deadline(),  # 180 seconds
            chain_id,
        )
    print("permit_data:", permit_data)
    print("signable_message:", signable_message)


    #signed_message = account.sign_message(signable_message)

    #amount = amount * 10**3 #adjust , convert it
    # Swap parameters
    amount_in = int(msg.amount * 10**6)  # 1 USDC 1 * 10**6 ,,, this should take .20 USDC
    #amount_in = amount * 10**6 does not tolerate floats
    
    min_amount_out = 1 * 10**12  # 0.00001 ETH (18 decimals, ~$2.50 at $2,500/ETH)
    path = [usdc_address, weth_address]  # USDC → WETH
    fee = 3000  # 0.3% fee tier for V3 pool

    # Approve Universal Router to spend USDC
    nonce = w3.eth.get_transaction_count(account.address, 'pending') #w3.eth.get_transaction_count(account.address)
    approve_tx = usdc_contract.functions.approve(ur_address, amount_in).build_transaction({
        "from": account.address,
        "gas": 250_000,
        "maxPriorityFeePerGas": w3.eth.max_priority_fee,
        "maxFeePerGas": w3.eth.gas_price*2,
        "nonce": nonce,
        "chainId": chain_id
    })
    signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, msg.private_key)
    approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
    print(f"Approval Tx Hash: {w3.to_hex(approve_tx_hash)}")
    w3.eth.wait_for_transaction_receipt(approve_tx_hash)

    # Encode swap and manual unwrap



    # Signing the message
    signed_message = account.sign_message(signable_message)
    print("signed_message:", signed_message)


    #print(dir(codec.encode.chain()))
    encoded_input = (
        codec
        .encode
        .chain()
        .permit2_permit(permit_data, signed_message)
        #.permit2_transfer_from(FunctionRecipient.SENDER,usdc_address,amount_in,FunctionRecipient.ROUTER)
        #.permit2_transfer_from(FunctionRecipient.ROUTER, usdc_address, amount_in)
        .v2_swap_exact_in(FunctionRecipient.ROUTER, amount_in, min_amount_out, path, fee,payer_is_sender=True)
        .unwrap_weth(FunctionRecipient.SENDER, 0)
        .build(codec.get_default_deadline())
    )

    # Transaction parameters
    trx_params = {
        "from": account.address,
        "to": ur_address,
        "gas": 500_000,  # Reduced but sufficient
        "maxPriorityFeePerGas": w3.eth.max_priority_fee,
        "maxFeePerGas": w3.eth.gas_price * 2,
        "type": '0x2',
        "chainId": chain_id,
        "value": 0,
        "nonce": w3.eth.get_transaction_count(account.address, 'pending'),#w3.eth.get_transaction_count(account.address),
        "data": encoded_input,
    }

    # Check USDC balance
    #usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    #if usdc_balance < amount_in:
    #    raise ValueError(f"Insufficient USDC: Balance {usdc_balance / 10**6}, Need {amount_in / 10**6}")

    # Send transaction
    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).rawTransaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    print(f"Swap Tx Hash: {w3.to_hex(trx_hash)}")
    print(f"Attempted to convert from USDC to ETH.")

    # Wait for confirmation
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    print(f"Status: {'Success' if receipt['status'] == 1 else 'Failed'}, Gas Used: {receipt['gasUsed']}")
    
    
    trxhash = "basescan.org/tx/"+str(w3.to_hex(trx_hash))
    rp = SwapCompleted(status = "success", message = "Successfully swapped ETH to USDC.", transaction = trxhash)
    await ctx.send(USERINPUT_AGENT,rp)


if __name__ == '__main__':
    agent2.run()
