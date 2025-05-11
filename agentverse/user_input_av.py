#agent1q2aczah05l97w8mnen2lcc59y052w8mphzwgv0q37npm9fml2fz5sw2s4vz av
#fetch1vtyrggrw3nhq3n4p49paum3tt6cwvq9vfga9rx av wallet
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model, Field

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address

from uagents.network import get_faucet, get_ledger
from uagents.agent import AgentRepresentation #to use txn wallet
from uagents.config import TESTNET_REGISTRATION_FEE

from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.wallet import LocalWallet

import os
import logging
from logging import Logger
import sys
import requests
import atexit
import time
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

# Agentverse agent addresses - Updated to match actual running agents
HEARTBEAT_AGENT="agent1q20850rnurygmuuu5v3ryzhxl2mrfnwler8gzc0h4u4xp4xxuruljj54rwp"
TOPUP_AGENT="agent1q08e85r72ywlp833e3gyvlvyu8v7h7d98l97xue8wkcurzk282r77sumaj7"
REWARD_AGENT="agent1qgywfpwj62l0jkwtwrqly8f3mz5j7qhxhz74ngf2h8pmagu3k282scgzpmj"
COININFO_AGENT="agent1qthmuhfu5xlu4s8uwlq7z2ghxhpdqpj2r8smaushxu0qr3k3zcwuxu87t0t"
CRYPTONEWS_AGENT="agent1qgy6eh453lucsvgg30fffd70umcq6fwt2wgx9ksyfxnw45wu4ravs26rvt6" #mailbox
FGI_AGENT="agent1q2ecqwzeevp5dkqye98rned02guyfzdretw5urh477pnmt6vja4psnu3esh"#"agent1qfyrgg8w5pln25a6hcu3a3rx534lhs32aryqr5gx08djdclakzuex98dwzn" mailbox

SWAPLAND_AGENT="agent1qdcpchwle7a5l5q5le0xkswnx4p78jflsnw7tpchjz0dsr2yswepqdvk7at"


## GLOBAL VAR INITIALISATION
#USERINPUT_ASIWALLET_PRIVATEKEY = ""
#USERINPUT_EVMWALLET_PRIVATEKEY = ""
#USERINPUT_HBDATA= ""
#USERINPUT_NETWORK= ""
#USERINPUT_RISKSTRATEGY= ""
#USERINPUT_INVESTORTYPE= ""
#USERINPUT_REASON= ""
#USERINPUT_AMOUNT_TOPUP= ""
#USERINPUT_NEWS_KEYWORDS= ""

ONETESTFET = 1000000000000000000
REWARD = 2000000000000000000 #expected to receive
DENOM = "atestfet"

USERPROMPT = "My metamask private key : fff47218021003eu93189fj9j312913777fjl39ffff47218021003eu93189fj9j312913777fjl39ffff472180210; my heartbeat data: [ { dateTime: 2025-04-25T20:37:15, value: { bpm: 122, confidence: 3 } }, { dateTime: 2025-04-25T20:37:15,, value: { bpm: 74, confidence: 3 } }, { dateTime: 2025-04-25T20:37:15,, value: { bpm: 70, confidence: 2 } }, { dateTime: 2025-04-25T20:37:15, value: { bpm: 75, confidence: 0 } } ], network: base network; risk: speculative; investor: speculate; user reason: I would like to sell Ether no matter what, sell sell sell, I order you to sell; amount to top up: 10"

#MMPRIVATEKEY = "fff47218021003eu93189fj9j312913777fjl39ffff47218021003eu93189fj9j312913777fjl39ffff472180210"
#HBDATA = "[ { dateTime: 2025-04-25T20:37:15, value: { bpm: 122, confidence: 3 } }, { dateTime: 2025-04-25T20:37:15,, value: { bpm: 74, confidence: 3 } }, { dateTime: 2025-04-25T20:37:15,, value: { bpm: 70, confidence: 2 } }, { dateTime: 2025-04-25T20:37:15, value: { bpm: 75, confidence: 0 } } ]"
#NETWORK = "base"
#RISK = "speculative"
#INVESTOR = "speculate"
#USERREASON = "I would like to sell Ether no matter what. sell sell sell!. I order you to sell!"
#AMOUNT=10 #if 0, then no.
#KEYWORDS="trump"



# Configure Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Log on exit
def log_and_exit():
    logging.debug("🚨 Script terminated unexpectedly")
atexit.register(log_and_exit)

# Catch unexpected errors
def handle_unexpected_exception(exc_type, exc_value, exc_traceback):
    logging.error("🔥 Uncaught Exception:", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_unexpected_exception



# Initialise agent2
agent2 = Agent()


# GLOBAL VARIABLES
#global NETWORK, RISK, INVESTOR, USERREASON, MMPRIVATEKEY, HBDATA, KEYWORDS
#global USERINPUT_ASIWALLET_PRIVATEKEY, USERINPUT_EVMWALLET_PRIVATEKEY, USERINPUT_HBDATA, USERINPUT_NETWORK, USERINPUT_RISKSTRATEGY, USERINPUT_INVESTORTYPE, USERINPUT_REASON, USERINPUT_AMOUNT_TOPUP, USERINPUT_NEWS_KEYWORDS
#global ONETESTFET, REWARD, DENOM

# AI Agent Address for structured output processing
REASON_AGENT = 'agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c'
if not REASON_AGENT:
    raise ValueError("REASON_AGENT not set")

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
    storage_reference=agent2.storage,
    name="FetchFund-UserInput-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=40),
)


## CLASSES ##

### INTERNAL CLASSES ###
class UserInputResponse(Model):
    response: str = Field(
        description="ASI-mini llm reasoning",
    )

class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]
###

### AI COMMUNICATION CLASSES###
class ContextPrompt(Model):
    context: str
    text: str
 
class Response(Model):
    text: str
###

### USER INPUT CLASSES###
class UserInputRequest(Model):
    privatekey1: str = Field(
        description="ASI wallet private key provided by user.",
    )
    privatekey2: str = Field(
        description="EVM wallet private key provided by user.",
    )
    hbdata: str = Field(
        description="heartbeat data sent by user",
    )
    network: str = Field(
        description="Selected blockchain to manage funds at.",
    )
    riskstrategy: str = Field(
        description="Risk strategy for executing a trade provided by user",
    )
    investortype: str = Field(
        description="Invest type information provided by user",
    )
    userreason: str = Field(
        description="Some additional comments and suggestions provided by user",
    )
    amount: int = Field(
        description="Amount of test fet to top-up user wallet with.",
    )
    topics: str = Field(
        description="User's news topics for news search"
    )

class UserOutputResponse(Model):
    response: str = Field(
        status="Response to user's query",
    )
###


### AGENTVERSE INTERACTION CLASSES ###

### HEARTBEAT AGENT ###
class HeartbeatRequest(Model):
    hbdata: str = Field(
        description="heartbeat data sent by user",
    )

class HeartbeatResponse(Model):
    status: str = Field(
        description="stop or continue",
    )

### TOPUP AGENT ###
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
    
### REWARD AGENT ###
class PaymentInquiry(Model):
    status: str

class PaymentRequest(Model):
    wallet_address: str
    amount: int
    denom: str
 
class TransactionInfo(Model):
    tx_hash: str
    
class PaymentReceived(Model):
    status: str
    
class RewardRequest(Model):
    status: str = Field(
        description="user requesting reward",
    )
    
### COININFO AGENT ###
class CoinInfoResponse(Model):
    name: str
    symbol: str
    current_price: float
    market_cap: float
    total_volume: float
    price_change_24h: float
    
class CoinInfoRequest(Model):
    blockchain: str = Field(
        description="Blockchain or crypto network name to check the price of its native coin",
    )


### CRYPTONEWS AGENT ###
class CryptonewsRequest(Model):
    limit: Optional[int] = 1
    keywords: str = Field(
        description="keywords separated with OR word"
    )

class CryptonewsResponse(Model):
    response: str = Field(
        description="All found recent news based on keywords provided.",
    )

### FGI AGENT ###
class FGIRequest(Model):
    limit: Optional[int] = 1

class FearGreedData(Model):
    value: float
    value_classification: str
    timestamp: str

class FGIResponse(Model):
    data: list[FearGreedData]
    status: str
    timestamp: str





# Startup Handler - Print agent details
@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")
    ctx.logger.info(f"My wallet address: {agent2.wallet.address()}")


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
            prompt = f'''Query provided by user - {item.text}. Try to match it with output schema model. If you think there is a missing data, fill the field with <UNKNOWN>.'''
            await ctx.send(REASON_AGENT, StructuredOutputPrompt(prompt=prompt, output_schema=UserInputRequest.schema()),)
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")



# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")


@struct_output_client_proto.on_message(StructuredOutputResponse)
async def handle_structured_output_response(ctx: Context, sender: str, msg: StructuredOutputResponse):
    
    global USERINPUT_ASIWALLET_PRIVATEKEY, USERINPUT_EVMWALLET_PRIVATEKEY, USERINPUT_HBDATA, USERINPUT_NETWORK, USERINPUT_RISKSTRATEGY, USERINPUT_INVESTORTYPE, USERINPUT_REASON, USERINPUT_AMOUNT_TOPUP, USERINPUT_NEWS_KEYWORDS
    
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
                "Sorry, I couldn't process your request. Please include a valid user input data matching the UserInputRequest model."
            ),
        )
        return

    try:

        # Parse the structured output to get the address
        asi_response = UserInputRequest.parse_obj(msg.output)
        
        USERINPUT_ASIWALLET_PRIVATEKEY = asi_response.privatekey1
        USERINPUT_EVMWALLET_PRIVATEKEY = asi_response.privatekey2
        USERINPUT_HBDATA = asi_response.hbdata
        USERINPUT_NETWORK = asi_response.network
        USERINPUT_RISKSTRATEGY = asi_response.riskstrategy
        USERINPUT_INVESTORTYPE = asi_response.investortype
        USERINPUT_REASON = asi_response.userreason
        USERINPUT_AMOUNT_TOPUP = asi_response.amount
        USERINPUT_NEWS_KEYWORDS=asi_response.topics

        #make sure amount is set to a value
        try:
            int(USERINPUT_AMOUNT_TOPUP)
            ctx.logger.info(f"Can be converted to integer: {USERINPUT_AMOUNT_TOPUP}.")
        except ValueError:
            ctx.logger.info("Cannot be converted to integer")
            USERINPUT_AMOUNT_TOPUP = 0

        #excluding AMOUNT as it can be equal to 0.
        if not all([USERINPUT_ASIWALLET_PRIVATEKEY, USERINPUT_EVMWALLET_PRIVATEKEY, USERINPUT_HBDATA, USERINPUT_NETWORK, USERINPUT_RISKSTRATEGY, USERINPUT_INVESTORTYPE, USERINPUT_REASON, USERINPUT_NEWS_KEYWORDS]):
           await ctx.send(session_sender,create_text_chat("Sorry, I couldn't find a valid user input data in your query."),)
           return

        #store the values
        ctx.storage.set("USERINPUT_ASIWALLET_PRIVATEKEY", asi_response.privatekey1)
        ctx.storage.set("USERINPUT_EVMWALLET_PRIVATEKEY", asi_response.privatekey2)
        #ctx.storage.set("USERINPUT_HBDATA", asi_response.hbdata)
        ctx.storage.set("USERINPUT_NETWORK", asi_response.network)
        ctx.storage.set("USERINPUT_RISKSTRATEGY", asi_response.riskstrategy)
        ctx.storage.set("USERINPUT_INVESTORTYPE", asi_response.investortype)
        ctx.storage.set("USERINPUT_REASON", asi_response.userreason)
        ctx.storage.set("USERINPUT_AMOUNT_TOPUP", asi_response.amount)
        ctx.storage.set("USERINPUT_NEWS_KEYWORDS", asi_response.topics)


        #final step to send the result:
        rp = "Launching FetchFund.."
        await ctx.send(session_sender, create_text_chat(rp),)

        #start the program
        #HEARTBEAT AGENT
        try:
            await ctx.send(HEARTBEAT_AGENT,HeartbeatRequest(hbdata=str(USERINPUT_HBDATA)))
        except Exception as e:
            ctx.logger.info(f"Error sending data to Heartbeat agent: {e}")
        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check the user input data provided. Please try again later."
            ),
        )
        return


#agentic interaction
@proto.on_message(UserInputRequest)
async def handle_request(ctx: Context, sender: str, msg: UserInputRequest):
    ctx.logger.info(f"User input data received: {msg}")

    global USERINPUT_ASIWALLET_PRIVATEKEY, USERINPUT_EVMWALLET_PRIVATEKEY, USERINPUT_HBDATA, USERINPUT_NETWORK, USERINPUT_RISKSTRATEGY, USERINPUT_INVESTORTYPE, USERINPUT_REASON, USERINPUT_AMOUNT_TOPUP, USERINPUT_NEWS_KEYWORDS

    try:
        USERINPUT_ASIWALLET_PRIVATEKEY = msg.privatekey1
        USERINPUT_EVMWALLET_PRIVATEKEY = msg.privatekey2
        USERINPUT_HBDATA = msg.hbdata
        USERINPUT_NETWORK = msg.network
        USERINPUT_RISKSTRATEGY = msg.riskstrategy
        USERINPUT_INVESTORTYPE = msg.investortype
        USERINPUT_REASON = msg.userreason
        USERINPUT_AMOUNT_TOPUP = msg.amount
        USERINPUT_NEWS_KEYWORDS=msg.topics
        #ctx.storage.set("SENDER_ADDRESS", sender)
        #prompt = f'''This is the data provided: {msg.riskstrategy}'''
    except:
        await ctx.send(sender,UserOutputResponse(response="Sorry, I couldn't find a valid user input data in your query."),)
        return

    try:
        int(USERINPUT_AMOUNT_TOPUP)
        ctx.logger.info(f"Can be converted to integer: {USERINPUT_AMOUNT_TOPUP}.")
    except ValueError:
        ctx.logger.info("Cannot be converted to integer.")
        USERINPUT_AMOUNT_TOPUP = 0
    
    if not all([USERINPUT_ASIWALLET_PRIVATEKEY, USERINPUT_EVMWALLET_PRIVATEKEY, USERINPUT_HBDATA, USERINPUT_NETWORK, USERINPUT_RISKSTRATEGY, USERINPUT_INVESTORTYPE, USERINPUT_REASON, USERINPUT_NEWS_KEYWORDS]):
        await ctx.send(sender,UserOutputResponse(response="Sorry, I couldn't find a valid user input data in your query."),)
        return

    #store the values
    ctx.storage.set("SENDER_ADDRESS", sender)

    ctx.storage.set("USERINPUT_ASIWALLET_PRIVATEKEY", msg.privatekey1)
    ctx.storage.set("USERINPUT_EVMWALLET_PRIVATEKEY", msg.privatekey2)
    #ctx.storage.set("USERINPUT_HBDATA"), msg.hbdata)
    ctx.storage.set("USERINPUT_NETWORK", msg.network)
    ctx.storage.set("USERINPUT_RISKSTRATEGY", msg.riskstrategy)
    ctx.storage.set("USERINPUT_INVESTORTYPE", msg.investortype)
    ctx.storage.set("USERINPUT_REASON", msg.userreason)
    ctx.storage.set("USERINPUT_AMOUNT_TOPUP", msg.amount)
    ctx.storage.set("USERINPUT_NEWS_KEYWORDS", msg.topics)

    await ctx.send(sender,UserOutputResponse(response="Launching FetchFund.."),)


    # HEARTBEAT AGENT
    try:
        await ctx.send(HEARTBEAT_AGENT,HeartbeatRequest(hbdata=str(USERINPUT_HBDATA),))
        rp = "Request to Heartbeat agent sent."
        ctx.logger.info(rp)
        await ctx.send(sender,UserOutputResponse(response=rp),)
    except Exception as e:
        rp = f"Error sending data to Heartbeat agent: {e}."
        ctx.logger.info(rp)
        await ctx.send(sender,UserOutputResponse(response=rp),)
        return
    

# HEARBEAT AGENT RESPONSE
# Waits for completion of heartbeat agent.
@agent2.on_message(model=HeartbeatResponse)
async def message_handler(ctx: Context, sender: str, msg: HeartbeatResponse):
    session_sender = ctx.storage.get(str(ctx.session))
    user_sender = ctx.storage.get("SENDER_ADDRESS")

    #ctx.logger.info(f"Session sender: {session_sender}")

    USERINPUT_AMOUNT_TOPUP = ctx.storage.get("USERINPUT_AMOUNT_TOPUP")
    USERINPUT_ASIWALLET_PRIVATEKEY = ctx.storage.get("USERINPUT_ASIWALLET_PRIVATEKEY")

    if (msg.status == "continue"):
        rp = f"Heartbeat agent: Received response - {msg.status}. Let's trade!"
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
            
        #execute topup_agent to receive funds
        ctx.logger.info(f"Amount to topup: {USERINPUT_AMOUNT_TOPUP}")

        if (int(USERINPUT_AMOUNT_TOPUP) > 0):#if 0 then top up not required
            agwall= (str)(agent2.wallet.address())
            try:
                await ctx.send(TOPUP_AGENT, TopupRequest(amount=USERINPUT_AMOUNT_TOPUP, agentwallet=agwall, fetwallet=USERINPUT_ASIWALLET_PRIVATEKEY))
                rp = f"Request to Topup Agent for receiving funds sent.."
                ctx.logger.info(rp)
                if session_sender is not None:
                    await ctx.send(session_sender, create_text_chat(rp),)
                else:
                    await ctx.send(user_sender,UserOutputResponse(response=rp),)
            except:
                rp = f"There was a problem with sending a request to Topup Agent."
                ctx.logger.info(rp)
                if session_sender is not None:
                    await ctx.send(session_sender, create_text_chat(rp),)
                else:
                    await ctx.send(user_sender,UserOutputResponse(response=rp),)
                return

        else:
            #execute reward_agent to pay fees for using swapland service. this might not be async though
            try:
                await ctx.send(REWARD_AGENT, PaymentInquiry(status = "ready"))
                rp = f"Request to Reward Agent for making a payment sent."
                ctx.logger.info(rp)
                if session_sender is not None:
                    await ctx.send(session_sender, create_text_chat(rp),)
                else:
                    await ctx.send(user_sender,UserOutputResponse(response=rp),)
            except Exception as e:
                rp = f"Failed to send request to Reward Agent to pay fees for using swapland services: {e}"
                ctx.logger.info(rp)
                if session_sender is not None:
                    await ctx.send(session_sender, create_text_chat(rp),)
                else:
                    await ctx.send(user_sender,UserOutputResponse(response=rp),)
                return

    else:
        rp = f"Heartbeat agent: Received response - {msg.status}. Cancelling the process.."
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
        return



#USER INPIT agent received requested funds
#TOPUP AGENT RESPONSE
@agent2.on_message(model=TopupResponse)
async def response_funds(ctx: Context, sender: str, msg: TopupResponse):
    """Handles topup response."""
    session_sender = ctx.storage.get(str(ctx.session))
    user_sender = ctx.storage.get("SENDER_ADDRESS")
    
    rp = f"Topup Agent: funds have been received successfully: {msg.status}"
    ctx.logger.info(rp)
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        await ctx.send(user_sender,UserOutputResponse(response=rp),)
        
    #execute reward_agent to pay fees for using swapland service. this might not be async though
    ledger: LedgerClient = get_ledger()
    agent_balance = ledger.query_bank_balance(Address(agent2.wallet.address()))/ONETESTFET
    
    rp = f"Balance after topup wallet: {agent_balance} TESTFET"
    ctx.logger.info(rp)
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        await ctx.send(user_sender,UserOutputResponse(response=rp),)

    try:
        await ctx.send(REWARD_AGENT, PaymentInquiry(status = "ready"))
        rp = f"Request to Reward Agent for making a payment sent."
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)

    except Exception as e:
        rp = f"Failed to send request Reward Agent to pay fees for using swapland services: {e}"
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
        return

# REWARD AGENT RESPONSE
#received request to make a payment for execution from reward_agent
@agent2.on_message(model=PaymentRequest)
async def message_handler(ctx: Context, sender: str, msg: PaymentRequest):
    session_sender = ctx.storage.get(str(ctx.session))
    user_sender = ctx.storage.get("SENDER_ADDRESS")

    rp = f"Payment request received: {msg}"
    ctx.logger.info(rp)
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        await ctx.send(user_sender,UserOutputResponse(response=rp),)
    
    #fees to pay
    fees = msg.amount/ONETESTFET
    #agent's balance
    ledger: LedgerClient = get_ledger()
    agent_balance = ledger.query_bank_balance(Address(agent2.wallet.address()))/ONETESTFET
    #instead i need to check here if the user agent has enough funds. if not, then return error, and finish the execution!
    
    if (agent_balance > fees):
        transaction = ctx.ledger.send_tokens(msg.wallet_address, msg.amount, msg.denom,agent2.wallet)
        rp = f"Transaction of {fees} has been sent: {transaction}."
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
    else:
        rp = f"Insufficient balance.. Please top it up!"
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
        return

    # send the tx hash so reward agent can confirm with fees payment
    await ctx.send(sender, TransactionInfo(tx_hash=transaction.tx_hash))


#confirmation from reward_agent after main agent paid fees for exection.
@agent2.on_message(model=PaymentReceived)
async def message_handler(ctx: Context, sender: str, msg: PaymentReceived):
    session_sender = ctx.storage.get(str(ctx.session))
    user_sender = ctx.storage.get("SENDER_ADDRESS")

    if (msg.status == "success"):
        rp = f"Fees transaction successful!"
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)

        ledger: LedgerClient = get_ledger()
        agent_balance = ledger.query_bank_balance(Address(agent2.wallet.address()))/ONETESTFET
        rp = f"Balance after fees: {agent_balance}"
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
        

        #start asi1 routine
        """Requests market data for the monitored coin once a day."""
        try:
            usernetwork = ctx.storage.get("USERINPUT_NETWORK")
            await ctx.send(COININFO_AGENT, CoinInfoRequest(blockchain=usernetwork))
            rp = f"Request to CoinInfo Agent sent."
            ctx.logger.info(rp)
            if session_sender is not None:
                await ctx.send(session_sender, create_text_chat(rp),)
            else:
                await ctx.send(user_sender,UserOutputResponse(response=rp),)

        except Exception as e:
            rp = f"Failed to send request to CoinInfo Agent: {e}."
            ctx.logger.info(rp)
            if session_sender is not None:
                await ctx.send(session_sender, create_text_chat(rp),)
            else:
                await ctx.send(user_sender,UserOutputResponse(response=rp),)
        
    else:
        rp = f"Fees transaction was unsuccessful!"
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
        return


# CoinInfo Agent response
@agent2.on_message(model=CoinInfoResponse)
async def coininfo_response(ctx: Context, sender: str, msg: CoinInfoResponse):
    session_sender = ctx.storage.get(str(ctx.session))
    user_sender = ctx.storage.get("SENDER_ADDRESS")

    rp = f"CoinInfo Agent response: {msg}."
    ctx.logger.info(rp)
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        await ctx.send(user_sender,UserOutputResponse(response=rp),)

    ctx.storage.set("ASI_COININFO", str(msg))

    try:
        kwords=ctx.storage.get("USERINPUT_NEWS_KEYWORDS")
        #temporary disabled cryptonews
        #await ctx.send(FGI_AGENT, FGIRequest()) #temporary call
        await ctx.send(CRYPTONEWS_AGENT, CryptonewsRequest(keywords=kwords))
        rp = f"Request to Cryptonews Agent sent."
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
    except Exception as e:
        rp = f"Error sending a request to Cryptonews Agent: {e}."
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
        return


# Cryptonews Agent response
@agent2.on_message(model=CryptonewsResponse)
async def handle_cryptonews_response(ctx: Context, sender: str, msg: CryptonewsResponse):
    """Handles cryptonews market data and requests FGI"""
    session_sender = ctx.storage.get(str(ctx.session))
    user_sender = ctx.storage.get("SENDER_ADDRESS")

    rp = f"Cryptonews Agent response: {msg}."
    ctx.logger.info(rp)
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        await ctx.send(user_sender,UserOutputResponse(response=rp),)

    ctx.storage.set("ASI_CRYPTONEWS", str(msg.response))

    try:
        await ctx.send(FGI_AGENT, FGIRequest())
        rp = f"Request to FGI Agent sent."
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
    except Exception as e:
        rp = f"Error sending a request to FGI Agent: {e}."
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
        return


# FGI Agent response
@agent2.on_message(model=FGIResponse)
async def handle_fgi_response(ctx: Context, sender: str, msg: FGIResponse):
    session_sender = ctx.storage.get(str(ctx.session))
    user_sender = ctx.storage.get("SENDER_ADDRESS")

    rp = f"FGI Agent response: {msg}."
    ctx.logger.info(rp)
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        await ctx.send(user_sender,UserOutputResponse(response=rp),)

    ctx.storage.set("ASI_FGI", str(msg))

    asi_fgi = ctx.storage.get("ASI_FGI")
    asi_cryptonews = ctx.storage.get("ASI_CRYPTONEWS")
    asi_coininfo = ctx.storage.get("ASI_COININFO")

    asi_network = ctx.storage.get("USERINPUT_NETWORK")
    asi_riskstrategy = ctx.storage.get("USERINPUT_RISKSTRATEGY")
    asi_investortype = ctx.storage.get("USERINPUT_INVESTORTYPE")
    asi_userreason = ctx.storage.get("USERINPUT_REASON")


    prompt = f'''Consider the following factors: Fear Greed Index Analysis - {asi_fgi}; Coin Market Data - {asi_coininfo}; Blockchain network - {asi_network}; User type of investing - {asi_investortype}; User risk strategy - {asi_riskstrategy}; Most recent crypto news - {asi_cryptonews}; User opinion - {asi_userreason}; '''
    context1 = '''You are a crypto expert, who is assisting the user to make the most meaningful decisions, to gain the most revenue.  Given the following information, respond with decision of either SELL, BUY or HOLD native token from given network. Inlcude your reasoning based on the analysed data and personal thoughts. Consider that the user cannot provide additional information. You could point out to questions which could help you making a solid decision.'''
    
    ctx.storage.set("ASI_COUNTER",4)
    
    try:
        await ctx.send(REASON_AGENT,ContextPrompt(context=context1, text=prompt))
        rp = f"Request sent to Reason Agent."
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
    except Exception as e:
        rp = f"Error sending a request to Reason Agent: {e}"
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
        return


@agent2.on_message(model=Response)
async def handle_request(ctx: Context, sender: str, msg: Response):
    session_sender = ctx.storage.get(str(ctx.session))
    user_sender = ctx.storage.get("SENDER_ADDRESS")
    asi_counter = ctx.storage.get("ASI_COUNTER")

    asi_fgi = ctx.storage.get("ASI_FGI")
    asi_cryptonews = ctx.storage.get("ASI_CRYPTONEWS")
    asi_coininfo = ctx.storage.get("ASI_COININFO")

    asi_network = ctx.storage.get("USERINPUT_NETWORK")
    asi_riskstrategy = ctx.storage.get("USERINPUT_RISKSTRATEGY")
    asi_investortype = ctx.storage.get("USERINPUT_INVESTORTYPE")
    asi_userreason = ctx.storage.get("USERINPUT_REASON")


    rp = f"Iteration {asi_counter}. Reason Agent response: {msg.text}."
    #ctx.logger.info(rp)
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        await ctx.send(user_sender,UserOutputResponse(response=rp),)


    prompt=""
    context1=""

    if (asi_counter > 1):
        ctx.storage.set("ASI_COUNTER",(asi_counter-1))
        prompt = f'''    Consider the following factors: Fear Greed Index Analysis - {asi_fgi}; Coin Market Data - {asi_coininfo}; Blockchain network - {asi_network}; User type of investing - {asi_investortype}; User risk strategy - {asi_riskstrategy}; Most recent crypto news - {asi_cryptonews}; User opinion - {asi_userreason}; '''
        context1 = f'''You are a crypto expert, who is assisting the user to make the most meaningful decisions, to gain the most revenue. This query has been analysed with the following reasoning: "{msg.text}". Given the following information and reasoning from other expert, respond with decision of either "SELL", "BUY" or "HOLD" native token from  "{asi_network}" network. Inlcude all of the reasoning based on the analysed data and personal thoughts. Consider that the information provided is the only input from the user, and the user cannot provide additional information. However, you could point out to the area or questions which could help you making a solid decision.'''
        try:
            await ctx.send(REASON_AGENT,ContextPrompt(context=context1, text=prompt))
            rp = f"Request sent to Reason Agent."
            ctx.logger.info(rp)
            if session_sender is not None:
                await ctx.send(session_sender, create_text_chat(rp),)
            else:
                await ctx.send(user_sender,UserOutputResponse(response=rp),)
        except Exception as e:
            rp = f"Error when sending a request to Reason agent: {e}."
            ctx.logger.info(rp)
            if session_sender is not None:
                await ctx.send(session_sender, create_text_chat(rp),)
            else:
                await ctx.send(user_sender,UserOutputResponse(response=rp),)
            return

    elif (asi_counter == 1):
        ctx.storage.set("ASI_COUNTER",(asi_counter-1))
        prompt = f'''    Consider the following factors: Fear Greed Index Analysis - {asi_fgi}; Coin Market Data - {asi_coininfo}; Blockchain network - {asi_network}; User type of investing - {asi_investortype}; User risk strategy - {asi_riskstrategy}; Most recent crypto news - {asi_cryptonews}; User opinion - {asi_userreason}; '''
        context1 = f'''You are an independent expert of a crypto market with knowledge of how worldwide politis affects the cryptomarket. You are assisting the user to make the most meaningful decisions, to gain the most revenue whilst minimising potential losses. This query has been analysed by other crypto experts, and here is a summery of their reasoning:"{msg.text}".;; FYI: SELL means swapping native crypto coin into USDC, BUY means swapping USDC into native crypto coin, HOLD means no actions. Given the following information and reasoning from other expert responses, make a decision by responding ONLY with one word "SELL", "BUY" or "HOLD" for a native token from given network. Again, your output is ether "SELL", "BUY" or "HOLD". '''
        try:
            await ctx.send(REASON_AGENT,ContextPrompt(context=context1, text=prompt))
            rp = f"Request sent to Reason Agent."
            ctx.logger.info(rp)
            if session_sender is not None:
                await ctx.send(session_sender, create_text_chat(rp),)
            else:
                await ctx.send(user_sender,UserOutputResponse(response=rp),)
        except Exception as e:
            rp = f"Error when sending a request to Reason agent: {e}."
            ctx.logger.info(rp)
            if session_sender is not None:
                await ctx.send(session_sender, create_text_chat(rp),)
            else:
                await ctx.send(user_sender,UserOutputResponse(response=rp),)
            return
    
    else:
        rp = f"Reason Agent iterations completed."
        ctx.logger.info(rp)
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            await ctx.send(user_sender,UserOutputResponse(response=rp),)


#########################################################################




# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)
agent2.include(struct_output_client_proto, publish_manifest=True)
agent2.include(proto, publish_manifest=True)

if __name__ == '__main__':
    agent2.run()
