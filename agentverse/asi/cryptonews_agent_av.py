#pip install newsapi-python
#agent1qgy6eh453lucsvgg30fffd70umcq6fwt2wgx9ksyfxnw45wu4ravs26rvt6 mailbox
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
from newsapi import NewsApiClient
from datetime import datetime, timedelta
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
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
CRYPTONEWS_SEED = os.getenv("CRYPTONEWS_SEED")

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


class CryptonewsRequest(Model):
    limit: Optional[int] = 1
    keywords: str = Field(
        description="keywords separated with OR word"
    )
    
class ASIRequest(Model):
    keywords: str = Field(
        description="keywords separated with OR word"
    )

class CryptonewsResponse(Model):
    response: str = Field(
        description="All found recent news based on keywords provided.",
    )

class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]


# Initialize Agent
agent2 = Agent(
    name="FetchFund - CryptoNews agent",
    port=8005,
    seed=CRYPTONEWS_SEED,
    mailbox = True,
    readme_path = "README_cryptonews.md",
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
    name="FetchFund-CryptoNews-Protocol",
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
            prompt = f"Try to identify keywords from user input, and return in output schema splitting it with OR word. This is user input: {item.text}."
            await ctx.send(
                AI_AGENT_ADDRESS,
                StructuredOutputPrompt(
                    prompt=prompt, output_schema=ASIRequest.schema()
                ),
            )
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
                "Sorry, I couldn't process your request. Please include a valid query for the cryptonews agent."
            ),
        )
        return

    try:
        # Parse the structured output to get the address
        cryptonews_request = ASIRequest.parse_obj(msg.output)
        cn = cryptonews_request.keywords

        if not cn:
            await ctx.send(session_sender,create_text_chat("Sorry, I couldn't find a valid query for the cryptonews agent. Please, enter keywords that you would like to query about."),)
            return
        #str(cn)
        response_text= str(get_recent_crypto_news(cryptonews_request.keywords))#might need another function that would take user keywords

        await ctx.send(session_sender, create_text_chat(response_text))
        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check the recent crypto news. Please try again later."
            ),
        )
        return





def get_recent_crypto_news(keywords : str,limit: int = 1) -> CryptonewsResponse:
    """Fetch crypto news data from NewsAPI"""
    
    today = datetime.today().strftime('%Y-%m-%d')# Get today's date
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')# Get yesterday's date by subtracting 1 day

    crypto_news=""
    news_output=""
    extracted_data = []
    try:
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)#"NEWS_API_KEY"
        
        #already a dictionary
        crypto_news = newsapi.get_everything(q=keywords,from_param=str(yesterday),to=str(today), sort_by = "relevancy", page_size=10, page=1, language="en")#recession, FOMC, crypto exchange, bearish, bullish, financial market
        
        logging.info(f"Found info: {crypto_news}")
        #we need to optimise the size, otherwise it may exceed ASI1 28000 tokens limit
        #news are delayed by 1 day with free version

        articles = crypto_news['articles']
        
        for article in articles:
            title = article.get('title')
            description = article.get('description')
            content = article.get('content')
            extracted_data.append({'title': title, 'description': description})#'content':content
        
        
    except Exception as e:
        logging.error(f"❌ Couldnt connect to NEWS_API: {e}")

        
    return json.dumps(extracted_data) #news_output
            #status="success",
            #timestamp=datetime.now(timezone.utc).isoformat()
        

@proto.on_message(model=CryptonewsRequest)
async def handle_message(ctx: Context, sender: str, msg: CryptonewsRequest):
    """Handle incoming messages requesting crypto news data"""
    logging.info(f"📩 Received message from {sender}: CryptonewsRequest for {msg.limit} entries")
    
    response = get_recent_crypto_news(msg.keywords,msg.limit)
    await ctx.send(sender, CryptonewsResponse(response=response))



# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)
agent2.include(struct_output_client_proto, publish_manifest=True)
agent2.include(proto, publish_manifest=True)



if __name__ == '__main__':
    agent2.run()
