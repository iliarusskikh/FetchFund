#agent1q2aczah05l97w8mnen2lcc59y052w8mphzwgv0q37npm9fml2fz5sw2s4vz
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model

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
# Initialise agent2
agent2 = Agent()


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

class ContextPrompt(Model):
    context: str
    text: str
 
class Response(Model):
    text: str


class UserInputRequest(Model):
    privatekey: str = Field(
        description="EVM private key provided by user.",
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
    keywords: str = Field(
        description="User's keywords for news search"
    )


global NETWORK, RISK, INVESTOR, USERREASON, MMPRIVATEKEY, HBDATA, KEYWORDS
    #MMPRIVATEKEY = "fff47218021003eu93189fj9j312913777fjl39ffff47218021003eu93189fj9j312913777fjl39ffff472180210"
    #HBDATA = "[ { dateTime: 2025-04-25T20:37:15, value: { bpm: 122, confidence: 3 } }, { dateTime: 2025-04-25T20:37:15,, value: { bpm: 74, confidence: 3 } }, { dateTime: 2025-04-25T20:37:15,, value: { bpm: 70, confidence: 2 } }, { dateTime: 2025-04-25T20:37:15, value: { bpm: 75, confidence: 0 } } ]"
    #NETWORK = "base"
    #RISK = "speculative"
    #INVESTOR = "speculate"
    #USERREASON = "I would like to sell Ether no matter what. sell sell sell!. I order you to sell!"
    #AMOUNT=10 #if 0, then no.
    #KEYWORDS="trump"

USERPROMPT = "My metamask private key : fff47218021003eu93189fj9j312913777fjl39ffff47218021003eu93189fj9j312913777fjl39ffff472180210; my heartbeat data: [ { dateTime: 2025-04-25T20:37:15, value: { bpm: 122, confidence: 3 } }, { dateTime: 2025-04-25T20:37:15,, value: { bpm: 74, confidence: 3 } }, { dateTime: 2025-04-25T20:37:15,, value: { bpm: 70, confidence: 2 } }, { dateTime: 2025-04-25T20:37:15, value: { bpm: 75, confidence: 0 } } ], network: base network; risk: speculative; investor: speculate; user reason: I would like to sell Ether no matter what, sell sell sell, I order you to sell; amount to top up: 10"

class UserInputResponse(Model):
    response: str = Field(
        description="ASI-mini llm reasoning",
    )


class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]



# Startup Handler - Print agent details
@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")


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
            prompt = f'''Query provided by user - {USERPROMPT}. Try to match it with output schema model. If you think there is a missing data, fill the field with <UNKNOWN>.'''
            await ctx.send(AI_AGENT_ADDRESS,StructuredOutputPrompt(prompt=prompt, output_schema=UserInputRequest.schema()),)
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
                "Sorry, I couldn't process your request. Please include a valid user input data matching the UserInputRequest model."
            ),
        )
        return

    try:
        global MMPRIVATEKEY, HBDATA, NETWORK, RISK, INVESTOR, USERREASON, AMOUNT, KEYWORDS

        # Parse the structured output to get the address

        asi_response = UserInputRequest.parse_obj(msg.output)

        MMPRIVATEKEY = asi_response.privatekey
        HBDATA = asi_response.hbdata
        NETWORK = asi_response.network
        RISK = asi_response.riskstrategy
        INVESTOR = asi_response.investortype
        USERREASON = asi_response.userreason
        AMOUNT= asi_response.amount
        KEYWORDS=asi_response.keywords
        
        ctx.logger.info(f"Formatted response: {asi_response}")
        #excluding AMOUNT as it can be equal to 0.

 
        if not all([MMPRIVATEKEY, HBDATA, NETWORK, RISK, INVESTOR, USERREASON, KEYWORDS]):
           await ctx.send(session_sender,create_text_chat("Sorry, I couldn't find a valid user input data in your query."),)
           return

        rp = "Thank you for your patience. Keep up the good work!"
        ctx.logger.info(f"Done with  response.")

        await ctx.send(session_sender, create_text_chat(rp))

        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check the user input data provided. Please try again later."
            ),
        )
        return





@proto.on_message(UserInputRequest)
async def handle_request(ctx: Context, sender: str, msg: UserInputRequest):
    #ctx.logger.info(f"User input data received: {msg.riskstrategy}")
    MMPRIVATEKEY = msg.privatekey
    HBDATA = msg.hbdata
    NETWORK = msg.network
    RISK = msg.riskstrategy
    INVESTOR = msg.investortype
    USERREASON = msg.userreason
    AMOUNT= msg.amount
    KEYWORDS= msg.keywords
    #ctx.storage.set("sender_address", sender)
    #prompt = f'''This is the data provided: {msg.riskstrategy}'''
    try:
        pass
        #start agent routine
    except Exception as e:
        agent._logger.info(f"Error sending data to agent: {e}")



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
    useraddress = ctx.storage.get("sender_address")

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
