#agent1qgywfpwj62l0jkwtwrqly8f3mz5j7qhxhz74ngf2h8pmagu3k282scgzpmj agentverse
#fetch1tj0ys9n80cja23er3azeska7tnufc25gw2nfj2 agentverse wallet

#this agent receives request to get the reward. upon request it checks storage fet, and send the , confirms with given agent address and sends the reward. test tokens for now
#requests fees as 6 TESTFET
#rewards main agent with 2 TESTFET
import argparse
import time
import os
import logging
from logging import Logger
import sys
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model
from uagents.network import wait_for_tx_to_complete
from uagents.setup import fund_agent_if_low

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address
from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.wallet import LocalWallet

from uagents.network import get_faucet, get_ledger
from uagents.agent import AgentRepresentation #to use txn wallet
from uagents.config import TESTNET_REGISTRATION_FEE
from uagents.utils import get_logger
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

# AI Agent Address for structured output processing
AI_AGENT_ADDRESS = 'agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c'
if not AI_AGENT_ADDRESS:
    raise ValueError("AI_AGENT_ADDRESS not set")

class RewardResponse(Model):
    response: str = Field(
        description="process user query and add response from ASI",
    )

class RewardRequest(Model):
    wallet_address: str = Field(
        description="wallet to receive the reward",
    )
    status: str = Field(
        description="user requesting reward",
    )
 
class PaymentRequest(Model):
    wallet_address: str
    amount: int
    denom: str
 
class TransactionInfo(Model):
    tx_hash: str

class PaymentInquiry(Model):
    status: str
 
class PaymentReceived(Model):
    status: str

ONETESTFET =1000000000000000000
UNCERTAINTYFET=10000000000000000 #to ease errors when stakign empties entire wallet
AMOUNT = 6000000000000000000
DENOM = "atestfet"
REWARD = 2000000000000000000


reward = Agent()

fund_agent_if_low(reward.wallet.address(), min_balance=AMOUNT)


@reward.on_event("startup")
async def introduce_agent(ctx: Context):
    """Logs agent startup details."""
    ctx.logger.info(f"Hello! My address is {reward.address}, my wallet address {reward.wallet.address()} ")

    reward._logger.info("🚀 Agent startup complete.")
    ledger: LedgerClient = get_ledger()
    agent_balance = ledger.query_bank_balance(Address(reward.wallet.address()))/ONETESTFET
    ctx.logger.info(f"My balance is {agent_balance} TESTFET")
    

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
    storage_reference=reward.storage,
    name="FethcFund-Reward-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=10),
)

class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]


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
            prompt = f'''You are a Reward agent of FetchFund system. This is your functions: Awaits requests from the Main Agent. Requests 6 TESTFET from the Main Agent as payment. Upon receipt, stakes the funds with a testnet validator and logs the transaction hash and payee in a local ledger (storage variable). At the end (post-swap), processes reward requests: Checks the ledger for the requester’s address. If found (payment confirmed), removes the address and sends 2 TESTFET back to the Main Agent. You can explain what you do or try to respond to the following user query : {item.text}'''
            await ctx.send(AI_AGENT_ADDRESS, StructuredOutputPrompt(prompt=prompt, output_schema=RewardResponse.schema()),)
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")



# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")


@struct_output_client_proto.on_message(StructuredOutputResponse)
async def handle_structured_output_response(
    ctx: Context, sender: str, msg: StructuredOutputResponse
):
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
                "Sorry, I couldn't process your request. Please include a valid query."
            ),
        )
        return

    try:
        # Parse the structured output to get the address
       reward_response = RewardResponse.parse_obj(msg.output)
       rw = reward_response.response
        
       if not rw:
           await ctx.send(session_sender,create_text_chat("Sorry, I couldn't understand your query."),)
           return

       await ctx.send(session_sender, create_text_chat(str(rw)))

        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check the reward agent query provided. Please try again later."
            ),
        )
        return





#main agent inquires to proceed with fees payment
@proto.on_message(model=PaymentInquiry)
async def send_payment(ctx: Context, sender: str, msg: PaymentInquiry):
    ctx.logger.info(f"Received payment request from {sender}: {msg}")
    if(msg.status == "ready"):
        await ctx.send(sender,PaymentRequest(wallet_address=str(reward.wallet.address()), amount=AMOUNT, denom=DENOM))#str(ctx.agent.address)


#successfully received fees from main agent
@reward.on_message(model=TransactionInfo)
async def confirm_transaction(ctx: Context, sender: str, msg: TransactionInfo):
    ctx.logger.info(f"Received transaction info from {sender}: {msg}")
    tx_resp = await wait_for_tx_to_complete(msg.tx_hash, ctx.ledger)
 
    coin_received = tx_resp.events["coin_received"]
    if (
            coin_received["receiver"] == str(reward.wallet.address())
            and coin_received["amount"] == f"{AMOUNT}{DENOM}"
    ):
        ctx.logger.info(f"Transaction was successful: {coin_received}")
    else:
        ctx.logger.info(f"Transaction was unsuccessful: {coin_received}")

    ledger: LedgerClient = get_ledger()
    agent_balance = (ledger.query_bank_balance(Address(reward.wallet.address())))/ONETESTFET
    ctx.logger.info(f"Balance after receiving fees: {agent_balance} TESTFET")

    #storage to verify for reward
    local_ledger = {"agent_address":sender, "tx":msg.tx_hash}
    ctx.storage.set("{ctx.agent.address}", local_ledger)#{ctx.agent.wallet.address()}
    
    await ctx.send(sender,PaymentReceived(status="success"))#str(ctx.agent.address)

    stakystake() #stake received amount of funds
        
    ledger_client = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    summary = ledger_client.query_staking_summary(reward.wallet.address())
    totalstaked = summary.total_staked/ONETESTFET
    ctx.logger.info(f"Received fees have been successfully staked.")
    ctx.logger.info(f"Staked: {totalstaked} TESTFET")
    agent_balance = (ledger.query_bank_balance(Address(reward.wallet.address())))/ONETESTFET
    ctx.logger.info(f"Available balance after staking: {agent_balance} TESTFET")


#main agent completed execution and requests the reward
@reward.on_message(model=RewardRequest)
async def request_reward(ctx: Context, sender: str, msg: RewardRequest):
    #fund_agent_if_low(reward.wallet.address(), min_balance=REWARD)
    if msg.status == "reward":
        check = ctx.storage.get("{ctx.agent.address}")
        if (check['agent_address'] == sender):
            transaction = ctx.ledger.send_tokens(msg.wallet_address, REWARD, DENOM, reward.wallet)#send the reward
            await ctx.send(sender, TransactionInfo(tx_hash=transaction.tx_hash))#str(ctx.agent.address)

            ctx.logger.info(f"Reward has been issued!")
            ctx.storage.remove("ctx.agent.address")#{ctx.agent.wallet.address()} #verification of completed transaction
        else:
            ctx.logger.info(f"Transaction not found!")
    else:
        ctx.logger.info(f"Incorrect status received!")
    

#when main agent receives the reward
@reward.on_message(model=PaymentReceived)
async def message_handler(ctx: Context, sender: str, msg: PaymentReceived):
    if (msg.status == "reward"):
        ctx.logger.info(f"Payment transaction successful!")
        ledger: LedgerClient = get_ledger()
        agent_balance = (ledger.query_bank_balance(Address(reward.wallet.address())))/ONETESTFET
        #print(f"Balance after fees: {agent_balance} TESTFET")
        agent_balance = agent_balance - REWARD #there is a delay in showing the transaction :(
        ctx.logger.info(f"Balance after issuing reward: {agent_balance} TESTFET")
    else:
        ctx.logger.info(f"Payment transaction unsuccessful!")


def stakystake():
    ledger: LedgerClient = get_ledger()

    agent_balance = ledger.query_bank_balance(Address(reward.wallet.address()))
    converted_balance = agent_balance/ONETESTFET - UNCERTAINTYFET
    
    #staking letsgooo
    ledger_client = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    validators = ledger_client.query_validators()
    # choose any validator
    validator = validators[2]
    #ctx.logger.info({validator.address})
    
    # delegate some tokens to this validator
    agent_balance = agent_balance - REWARD #leave the reward amount of funds to further issue to main agent
    tx = ledger_client.delegate_tokens(validator.address, agent_balance, reward.wallet)
    tx.wait_to_complete()
    reward._logger.info("Delegation completed.")

 

# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
reward.include(chat_proto, publish_manifest=True)
reward.include(struct_output_client_proto, publish_manifest=True)
reward.include(proto, publish_manifest=True)



if __name__ == "__main__":
    reward.run()
