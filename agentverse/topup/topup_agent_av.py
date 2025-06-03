#agent1q08e85r72ywlp833e3gyvlvyu8v7h7d98l97xue8wkcurzk282r77sumaj7
from logging import Logger
import logging
import random
import sys
import os

from datetime import datetime
from uuid import uuid4

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

from uagents.experimental.quota import QuotaProtocol, RateLimit

# Import the necessary components of the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

#loop = asyncio.get_event_loop()

class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]


class TopupRequest(Model):
    amount: float = Field(
        description="Requested amount of FET",
    )
    agentwallet: str = Field(
        description="Recepient wallet address",
    )
    fetwallet: str = Field(
        description="User's ASI wallet to send the funds from",
    )

class TopupResponse(Model):
    status: str = Field(
        description="Successful completion status",
    )
 
class TopupResponseChat(Model):
    response: str = Field(
        description="Response from ASI1 LLM",
    )

#AUTOAGENT_SEED = "this is just test listen up this is test"

# AI Agent Address for structured output processing
AI_AGENT_ADDRESS = 'agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c'
if not AI_AGENT_ADDRESS:
    raise ValueError("AI_AGENT_ADDRESS not set")

farmer = Agent()

ONETESTFET=1000000000000000000
UNCERTAINTYFET=1000000000000000


def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)
struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)
proto = QuotaProtocol(
    storage_reference=farmer.storage,
    name="FethcFund-Topup-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=10),
)


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




# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Got a message from {sender}: {msg}")
    ctx.storage.set(str(ctx.session), sender)
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Got a start session message from {sender}")
            continue
        elif isinstance(item, TextContent):
            ctx.logger.info(f"Got a message from {sender}: {item.text}")
            ctx.storage.set(str(ctx.session), sender)
            #prompt = f'''Message received from user: {item.text}. Greet the user. You are a top-up agent, part of FetchFund system. User cannot interact with this agent via Chat Protocol. They need to implement class TopupRequest(Model) and class TopupResponse(Model) for their agent.'''
            prompt =f'''{item.text}.'''
            await ctx.send(
                AI_AGENT_ADDRESS,
                StructuredOutputPrompt(
                    #prompt=prompt, output_schema=TopupResponseChat.schema()
                    prompt=prompt, output_schema=TopupRequest.schema()
                ),)
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")


# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")



@struct_output_client_proto.on_message(StructuredOutputResponse)
async def handle_structured_output_response(ctx: Context, sender: str, msg: StructuredOutputResponse):
    session_sender = ctx.storage.get(str(ctx.session))
    if session_sender is None:
        ctx.logger.error(
            "Discarding message because no session sender found in storage"
        )
        return

    if "<UNKNOWN>" in str(msg.output):
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't process your request. Please, include a valid prompt text to match TopupRequest(Model). Provide the following parameters: amount, agent wallet, asi fet wallet."
            ),
        )
        return

    try:
       # Parse the structured output to get the address
       #topup_request = TopupResponseChat.parse_obj(msg.output)
       #tp = topup_request.response
       topup_request = TopupRequest.parse_obj(msg.output)
       am = topup_request.amount
       ag = topup_request.agentwallet
       fe = topup_request.fetwallet
       
       addition=""

       if am >15:
        topup_request.amount = 15
        addition = "The maximum amount per transaction is 15 TESTFET! Please, do not overuse this service."

       ctx.logger.info(f"Received formatted request: {topup_request}")

       if not all([am, ag, fe]):
            await ctx.send(session_sender, create_text_chat("Sorry, I couldn't find a valid response for your query that would have matched TopupRequest(Model)."))
            return

       await chat_request_funds(ctx, sender, topup_request)

       endoftransaction ="You agent wallet has been topped up! "+addition+" Thank you for using this service :)"
       await ctx.send(session_sender, create_text_chat(str(endoftransaction)))
        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't read your query. Please try again later."
            ),
        )
        return


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

            farmer._logger.info(f"Staked: {totalstaked} TESTFET")

        #print("Doing hard work...")
        #await asyncio.sleep(10)#36000


 
 
#idealy should be sending funds from the FET wallet, on mainnet. but lets farm for now
@proto.on_message(model=TopupRequest)
async def request_funds(ctx: Context, sender: str, msg: TopupRequest):
    """Handles topup requests Topup."""
        
    ledger: LedgerClient = get_ledger()
    #faucet: FaucetApi = get_faucet()

    sender_balance = ledger.query_bank_balance(Address(msg.agentwallet))/ONETESTFET#ctx.agent.wallet.address()
    #fetwallet_balance = ledger.query_bank_balance(Address(msg.fetwallet))/ONETESTFET#ctx.agent.wallet.address()
    #ctx.logger.info({fetwallet_balance})
    ctx.logger.info(f'''Sender balance is: {sender_balance}''')

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



#chat interaction function
async def chat_request_funds(ctx: Context, sender: str, msg: TopupRequest):
    """Handles topup requests Topup."""
    ctx.logger.info(f"Inside the function: {msg}")
    ledger: LedgerClient = get_ledger()

    sender_balance = ledger.query_bank_balance(Address(msg.agentwallet))/ONETESTFET#ctx.agent.wallet.address()
    #fetwallet_balance = ledger.query_bank_balance(Address(msg.fetwallet))/ONETESTFET#ctx.agent.wallet.address()
    ctx.logger.info(f'''Sender balance is: {sender_balance}''')


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


# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
farmer.include(chat_proto, publish_manifest=True)
farmer.include(struct_output_client_proto, publish_manifest=True)
farmer.include(proto, publish_manifest=True)



if __name__ == "__main__":
    farmer.run()
    #print("Starting the external loop from the agent or bureau...")
    farmer._logger.info("Starting agent..")

    #loop.create_task(get_faucet_farmer())
    # > when attaching the agent to the external loop
    #loop.create_task(farmer.run_async())
    #with contextlib.suppress(KeyboardInterrupt):
    #    loop.run_forever()

    
