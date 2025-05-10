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
COIN_AGENT="agent1qthmuhfu5xlu4s8uwlq7z2ghxhpdqpj2r8smaushxu0qr3k3zcwuxu87t0t"
CRYPTONEWS_AGENT="agent1qgy6eh453lucsvgg30fffd70umcq6fwt2wgx9ksyfxnw45wu4ravs26rvt6"
FGI_AGENT="agent1q2ecqwzeevp5dkqye98rned02guyfzdretw5urh477pnmt6vja4psnu3esh"#"agent1qfyrgg8w5pln25a6hcu3a3rx534lhs32aryqr5gx08djdclakzuex98dwzn" mailbox
REASON_AGENT="agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c" #ASI:One

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
AI_AGENT_ADDRESS = 'agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c'
if not AI_AGENT_ADDRESS:
    raise ValueError("AI_AGENT_ADDRESS not set")

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
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=10),
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
            await ctx.send(AI_AGENT_ADDRESS, StructuredOutputPrompt(prompt=prompt, output_schema=UserInputRequest.schema()),)
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

        ctx.logger.info("Done with response.")

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

    ctx.storage.set("USERINPUT_ASIWALLET_PRIVATEKEY", asi_response.privatekey1)
    ctx.storage.set("USERINPUT_EVMWALLET_PRIVATEKEY", asi_response.privatekey2)
    #ctx.storage.set("USERINPUT_HBDATA"), asi_response.hbdata)
    ctx.storage.set("USERINPUT_NETWORK", asi_response.network)
    ctx.storage.set("USERINPUT_RISKSTRATEGY", asi_response.riskstrategy)
    ctx.storage.set("USERINPUT_INVESTORTYPE", asi_response.investortype)
    ctx.storage.set("USERINPUT_REASON", asi_response.userreason)
    ctx.storage.set("USERINPUT_AMOUNT_TOPUP", asi_response.amount)
    ctx.storage.set("USERINPUT_NEWS_KEYWORDS", asi_response.topics)

    await ctx.send(sender,UserOutputResponse(response="Launching FetchFund.."),)


    # HEARTBEAT AGENT
    try:
        await ctx.send(HEARTBEAT_AGENT,HeartbeatRequest(hbdata=str(USERINPUT_HBDATA),))
    except Exception as e:
        ctx.logger.info(f"Error sending data to Heartbeat agent: {e}")
    



# HEARBEAT AGENT RESPONSE
# Waits for completion of heartbeat agent.
@agent2.on_message(model=HeartbeatResponse)
async def message_handler(ctx: Context, sender: str, msg: HeartbeatResponse):
    session_sender = ctx.storage.get(str(ctx.session))
    ctx.logger.info(f"Session sender: {session_sender}")

    USERINPUT_AMOUNT_TOPUP = ctx.storage.get("USERINPUT_AMOUNT_TOPUP")
    USERINPUT_ASIWALLET_PRIVATEKEY = ctx.storage.get("USERINPUT_ASIWALLET_PRIVATEKEY")

    if (msg.status == "continue"):
        ctx.logger.info(f"Heartbeat agent: Received response - {msg.status}. Let's trade!")
        
        rp = f"Heartbeat agent: Received response - {msg.status}. Let's trade!"
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            user_sender = ctx.storage.get("SENDER_ADDRESS")
            await ctx.send(user_sender,UserOutputResponse(response=rp),)
            
        #execute topup_agent to receive funds
        ctx.logger.info(f"Amount to topup: {USERINPUT_AMOUNT_TOPUP}")
        USERINPUT_AMOUNT_TOPUP
        if (int(USERINPUT_AMOUNT_TOPUP) > 0):#if 0 then top up not required
            agwall= (str)(agent2.wallet.address())
            try:
                await ctx.send(TOPUP_AGENT, TopupRequest(amount=USERINPUT_AMOUNT_TOPUP, agentwallet=agwall, fetwallet=USERINPUT_ASIWALLET_PRIVATEKEY))
                rp = f"Request to Topup Agent for receiving funds sent.."
                if session_sender is not None:
                    await ctx.send(session_sender, create_text_chat(rp),)
                else:
                    user_sender = ctx.storage.get("SENDER_ADDRESS")
                    await ctx.send(user_sender,UserOutputResponse(response=rp),)
            except:
                rp = f"There was a problem with sending a request to Topup Agent."
                if session_sender is not None:
                    await ctx.send(session_sender, create_text_chat(rp),)
                else:
                    user_sender = ctx.storage.get("SENDER_ADDRESS")
                    await ctx.send(user_sender,UserOutputResponse(response=rp),)

        else:
            #execute reward_agent to pay fees for using swapland service. this might not be async though
            try:
                pass
                #await ctx.send(REWARD_AGENT, PaymentInquiry(ready = "ready"))
                ctx.logger.info(f"Ready to pay status sent")
            except Exception as e:
                logging.error(f"Failed to send request to Reward Agent to pay fees for using swapland services: {e}")


    else:
        ctx.logger.info(f"Heartbeat agent: Received response - {msg.status}. Cancelling the process..")
        rp = f"Heartbeat agent: STOP received: canceling the process..: {msg.status}"
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            user_sender = ctx.storage.get("SENDER_ADDRESS")
            await ctx.send(user_sender,UserOutputResponse(response=rp),)



#USER INPIT agent received requested funds
#TOPUP AGENT RESPONSE
@agent2.on_message(model=TopupResponse)
async def response_funds(ctx: Context, sender: str, msg: TopupResponse):
    """Handles topup response."""
    session_sender = ctx.storage.get(str(ctx.session))
    ctx.logger.info(f"📩 User's wallet topped up: {msg.status}.")
    
    rp = f"Funds have been received successfully: {msg.status}."
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        user_sender = ctx.storage.get("SENDER_ADDRESS")
        await ctx.send(user_sender,UserOutputResponse(response=rp),)
        
    #execute reward_agent to pay fees for using swapland service. this might not be async though
    ledger: LedgerClient = get_ledger()
    agent_balance = ledger.query_bank_balance(Address(agent2.wallet.address()))/ONETESTFET
    
    ctx.logger.info(f"Balance after topup wallet: {agent_balance} TESTFET")
    rp = f"Balance after topup wallet: {agent_balance} TESTFET"
    if session_sender is not None:
        await ctx.send(session_sender, create_text_chat(rp),)
    else:
        user_sender = ctx.storage.get("SENDER_ADDRESS")
        await ctx.send(user_sender,UserOutputResponse(response=rp),)

    try:
        pass
        #await ctx.send(REWARD_AGENT, PaymentInquiry(ready = "ready"))
        ctx.logger.info(f"Ready to pay status sent")
        rp = f"Ready to pay status sent to Reward Agent.."
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            user_sender = ctx.storage.get("SENDER_ADDRESS")
            await ctx.send(user_sender,UserOutputResponse(response=rp),)

    except Exception as e:
        ctx.logger.error(f"Failed to send request Reward Agent to pay fees for using swapland services: {e}")
        rp = f"Failed to send request Reward Agent to pay fees for using swapland services: {e}"
        if session_sender is not None:
            await ctx.send(session_sender, create_text_chat(rp),)
        else:
            user_sender = ctx.storage.get("SENDER_ADDRESS")
            await ctx.send(user_sender,UserOutputResponse(response=rp),)





#@agent2.on_message(UserInputRequest, replies={ContextPrompt})
    #try:
   #     pass
        #start agent routine
        #await ctx.send(AI_AGENT_ADDRESS,ContextPrompt(context="You need to analyse the user input provided and match the output schema. If you think there is a missing data, fill the field with <UNKNOWN>. ", text=prompt))
   # except Exception as e:
    #    agent._logger.info(f"Error sending data to agent: {e}")

#I DO NOT NEED THIS ACTUALLY
@agent2.on_message(Response, replies={UserInputResponse})
async def handle_request(ctx: Context, sender: str, msg: Response):
    ctx.logger.info(f"This is the ASI-mini formatted output: {msg.text}")
    useraddress = ctx.storage.get("SENDER_ADDRESS")

    try:
        await ctx.send(useraddress,UserInputResponse(status=msg.text))
    except Exception as e:
        agent._logger.info(f"Error sending data to agent: {e}")
#########################################################################








# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)
agent2.include(struct_output_client_proto, publish_manifest=True)
agent2.include(proto, publish_manifest=True)

if __name__ == '__main__':
    agent2.run()
