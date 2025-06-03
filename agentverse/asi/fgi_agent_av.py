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
from datetime import datetime, timedelta, timezone
from typing import Any

# Import the necessary components of the chat protocol
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
CMC_API_KEY = "09ff35a0-3123-438a-98aa-68e0b56380bf"#os.getenv("CMC_API_KEY")
if not CMC_API_KEY:
    logging.error("❌ CMC_API_KEY is not set. Please set it in environment variables.")
    sys.exit(1)

#FGI_SEED = os.getenv("FGI_SEED")
#if not FGI_SEED:
#    sys.exit(1)
#    logging.error("❌ FGI_SEED is not set. Please set it in environment variables.")

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


class ASIRequest(Model):
    keywords: str = Field(
        description="keywords separated with OR word"
    )


# Initialize Agent
agent2 = Agent(
    #name="FetchFund - Fear and Greed Index agent",
    #port=8006,
    #seed=FGI_SEED,
    #mailbox = True,
    #readme_path = "README_fgi.md"
    )


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
    name="FetchFund-FGI-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=10),
)



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
    await ctx.send(sender,ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),)
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Got a start session message from {sender}")
            continue
        elif isinstance(item, TextContent):
            session_sender = ctx.storage.get(str(ctx.session))
            ctx.logger.info(f"Got a message from {sender}: {item.text}")
            ctx.storage.set(str(ctx.session), sender)
            response_text = await process_response(ctx, FGIRequest())
    
            await ctx.send(session_sender, create_text_chat(str(response_text)))

        else:
            ctx.logger.info(f"Got unexpected content from {sender}")



# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

    
def get_fear_and_greed_index(limit: int = 1) -> FGIResponse:
    """Fetch Fear and Greed index data from CoinMarketCap API"""
    url = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical"

    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    
    params = {"limit": limit}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises error for non-200 status codes
        
        raw_data = response.json()
        fear_greed_data = []

        for entry in raw_data.get("data", []):
            data = FearGreedData(
                value=entry["value"],
                value_classification=entry["value_classification"],
                timestamp=entry["timestamp"]
            )
            fear_greed_data.append(data)

        #return FGIResponse(
        #    data=fear_greed_data,
        #    status="success",
        #    timestamp=datetime.utcnow(timezone.utc).isoformat()
        #)
        
        return FGIResponse(
            data=fear_greed_data,
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    except requests.exceptions.RequestException as e:
        logging.error(f"⚠️ API Request Failed: {e}")
        return FGIResponse(data=[], status="error", timestamp=datetime.utcnow().isoformat())



async def process_response(ctx: Context, msg: FGIRequest) -> FGIResponse:
    """Process the request and return formatted response"""
    logging.debug("🔄 Processing request...")

    fear_greed_data = get_fear_and_greed_index(msg.limit)
    
    for entry in fear_greed_data.data:
        ctx.logger.info(f"📊 Fear and Greed Index: {entry.value}")
        ctx.logger.info(f"🔍 Classification: {entry.value_classification}")
        ctx.logger.info(f"⏳ Timestamp: {entry.timestamp}")
    
    return fear_greed_data


@proto.on_message(model=FGIRequest)
async def handle_message(ctx: Context, sender: str, msg: FGIRequest):
    """Handle incoming messages requesting Fear and Greed index data"""
    ctx.logger.info(f"📩 Received message from {sender}: FGIRequest for {msg.limit} entries")
    logging.info(f"📩 Received message from {sender}: FGIRequest for {msg.limit} entries")
    
    response = await process_response(ctx, msg)
    
    await ctx.send(sender, response)

    return response



# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)
agent2.include(struct_output_client_proto, publish_manifest=True)
agent2.include(proto, publish_manifest=True)



if __name__ == '__main__':
    agent2.run()
