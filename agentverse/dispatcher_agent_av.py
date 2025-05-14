# "agent1qw7k3cfqnexa08a3wwuggznd3cduuse469uz7kja6ugn85erdjnsqc7ap9a" mailbox
from datetime import datetime
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

from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()
# Ensure API key is loaded
DISPATCHER_SEED = os.getenv("DISPATCHER_SEED")


def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )


# Initialize Agent
agent2 = Agent(
    name="FetchFund - Dispatcher Agent",
    port=8010,
    seed=DISPATCHER_SEED,
    mailbox = True,
    #readme_path = "README_dispatcher.md",
    )



# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)
struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)

proto = QuotaProtocol(
    storage_reference=agent2.storage,
    name="FetchFund-CryptoNews-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=40),
)


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




class DispatcherCompleted(Model):
    status: str= Field(
        description="Status response from Swapland Agent",
    )
    message: str = Field(
        description="Additional information",
    )
    sessionsender : str
    


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
    
    
class DispatcherRequest(Model):
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
    transaction : str = Field(
        description="Transaction info",
    )
    sessionsender : str = Field(
        description="Required to preserve a session sender",
    )


class DispatcherResponse(Model):
    status : str = Field(
        description="Status response from Swapland Agent",
    )
    sessionsender : str = Field(
        description="Required to preserve a session sender",
    )

seshsender = ""

    


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




# AI Agent Address for structured output processing
USERINPUT_AGENT_ADDRESS = 'agent1q2aczah05l97w8mnen2lcc59y052w8mphzwgv0q37npm9fml2fz5sw2s4vz'
SWAPLAND_AGENT_ADDRESS = 'agent1qt3vcc28ykzrnacsy5nj6k7c88c8r48esp6n25vc0cgtmzwl4m7jcaqvh8c'



# Startup Handler - Print agent details
@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    logging.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")


@proto.on_message(model=DispatcherRequest)
async def message_handler(ctx: Context, sender: str, msg: DispatcherRequest):
    logging.info(f"{msg}")
    global seshsender
    seshsender = msg.sessionsender

    await ctx.send(SWAPLAND_AGENT_ADDRESS, SwaplandRequest(blockchain=msg.blockchain, signal=msg.signal, amount = msg.amount, private_key = msg.private_key))

@proto.on_message(model=SwaplandResponse)
async def message_handler(ctx: Context, sender: str, msg: SwaplandResponse):
    logging.info(f"{msg}")
    await ctx.send(USERINPUT_AGENT_ADDRESS, DispatcherResponse(status = msg.status, sessionsender = seshsender))


@proto.on_message(model=SwapCompleted)
async def message_handler(ctx: Context, sender: str, msg: SwapCompleted):
    logging.info(f"{msg}")
    await ctx.send(USERINPUT_AGENT_ADDRESS, DispatcherCompleted(status = msg.status,message = msg.message, transaction = msg.transaction, sessionsender = seshsender))
 

agent2.include(proto, publish_manifest=True)


if __name__ == '__main__':
    agent2.run()
