#agent1q08e85r72ywlp833e3gyvlvyu8v7h7d98l97xue8wkcurzk282r77sumaj7 agentverse
from logging import Logger
import logging
import random
import sys
import os
from dotenv import load_dotenv

import argparse
import time
#import asyncio
#import contextlib

from uagents import Agent, Context, Protocol, Model, Field
from uagents.config import TESTNET_REGISTRATION_FEE
from uagents.network import get_faucet, get_ledger
from uagents.utils import get_logger
from uagents.agent import AgentRepresentation #to use txn wallet
from uagents.setup import fund_agent_if_low

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address
from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.wallet import LocalWallet

#loop = asyncio.get_event_loop()

class TopupRequest(Model):
    amount: float
    agentwallet: str
    fetwallet: str

class TopupResponse(Model):
    status: str
 

#load_dotenv()
#AUTOAGENT_SEED = "this is just test listen up this is test"

farmer = Agent()

ONETESTFET=1000000000000000000
UNCERTAINTYFET=1000000000000000

fund_agent_if_low(farmer.wallet.address())
 
@farmer.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(farmer.address)
    ctx.logger.info(farmer.wallet.address())
    
    #agent1 = Agent(
    #name="Autovar - Test agent",
    #seed=AUTOAGENT_SEED
    #)
    #await asyncio.sleep(5)
    #@agent1.on_event("startup")
    #async def introduce_agent(ctx: Context):
    #    ctx.logger.info(f"Hello, I'm agent {ctx.agent.name} and I am starting up")


#@farmer.on_interval(12000)
#async def stakeupdate(ctx: Context):#ctx: Context
#        ledger: LedgerClient = get_ledger()#"mainnet"
#        agent_balance = ledger.query_bank_balance(Address(farmer.wallet.address()))
#        converted_balance = agent_balance/ONETESTFET
#        ctx.logger.info(f"Received: {converted_balance} TESTFET")


@farmer.on_interval(12000)
async def get_faucet_farmer(ctx: Context):#ctx: Context
    #while True:
        ledger: LedgerClient = get_ledger()#"mainnet"
        faucet: FaucetApi = get_faucet()
        #fund_agent_if_low(farmer.wallet.address())
        faucet.get_wealth(farmer.wallet.address())
        agent_balance = ledger.query_bank_balance(Address(farmer.wallet.address()))
        converted_balance = agent_balance/ONETESTFET
        
        #logging.info(f"Received: {converted_balance} TESTFET")
        farmer._logger.info(f"Received: {converted_balance} TESTFET")

        #ctx.logger.info(f"Received: {converted_balance} TESTFET")
    
        #ctx.logger.info({agent_balance})
        
        #staking letsgooo
        #ledger_client = LedgerClient(NetworkConfig.fetchai_stable_testnet())
        #faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
        #validators = ledger.query_validators()
        # choose any validator
        #validator = validators[2]
        #ctx.logger.info({validator.address})
        
        
        if (converted_balance >1):
            # delegate some tokens to this validator
            agent_balance = agent_balance - UNCERTAINTYFET
            #tx = ledger_client.delegate_tokens(validator.address, agent_balance, farmer.wallet)
            #tx.wait_to_complete()
            
            #then call function to stake
            #ctx.logger.info("Delegation completed.")
            summary = ledger.query_staking_summary(farmer.wallet.address())
            totalstaked = summary.total_staked/ONETESTFET
            #ctx.logger.info(f"Staked: {totalstaked} TESTFET")
            #logging.info(f"Staked: {totalstaked} TESTFET")
            farmer._logger.info(f"Staked: {totalstaked} TESTFET")

        #print("Doing hard work...")
        #await asyncio.sleep(10)#36000


 
 
#idealy should be sending funds from the FET wallet, on mainnet. but lets farm for now
@farmer.on_message(model=TopupRequest)
async def request_funds(ctx: Context, sender: str, msg: TopupRequest):
    """Handles topup requests Topup."""
        
    ledger: LedgerClient = get_ledger()
    #faucet: FaucetApi = get_faucet()

    sender_balance = ledger.query_bank_balance(Address(msg.agentwallet))/ONETESTFET#ctx.agent.wallet.address()
    #fetwallet_balance = ledger.query_bank_balance(Address(msg.fetwallet))/ONETESTFET#ctx.agent.wallet.address()
    #ctx.logger.info({fetwallet_balance})
    ctx.logger.info({sender_balance})

    amo = int(msg.amount * ONETESTFET) #5 TESTFET
    deno = 'atestfet'
    
    try:
        #transaction = ctx.ledger.send_tokens(msg.agentwallet, amo, deno,msg.fetwallet)
        transaction = ctx.ledger.send_tokens(msg.agentwallet, amo, deno,farmer.wallet)
    except Exception as e:
        ctx.logger.error(f" Error sending tokens: {e}")

    sender_balance = ledger.query_bank_balance(Address(msg.agentwallet))/ONETESTFET
    sender_balance = sender_balance + amo/ONETESTFET
    ctx.logger.info(f"📩 After funds received: {sender_balance}")

    #ctx.logger.info({sender_balance})
    #await asyncio.sleep(5)
    
    try:
        await ctx.send(sender, TopupResponse(status="Success!"))
    except Exception as e:
        #logging.error(f" Error sending TopupResponse: {e}")
        ctx.logger.error(f" Error sending TopupResponse: {e}")



if __name__ == "__main__":
    farmer.run()
    print("Starting the external loop from the agent or bureau...")
    farmer._logger.info("Starting agent..")

    #loop.create_task(get_faucet_farmer())
    # > when attaching the agent to the external loop
    #loop.create_task(farmer.run_async())
    #with contextlib.suppress(KeyboardInterrupt):
    #    loop.run_forever()
