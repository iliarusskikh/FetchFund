#agent1qfqf3mj9c0gd4afl93khpvsq0lc2mgph2n7ypd6mslc3uv9pzcphueshk2m mailbox
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
from llm_swapfinder import query_llm


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
SWAPLAND_SEED = os.getenv("SWAPLAND_SEED")


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

class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]


# Initialize Agent
agent2 = Agent(
    name="FetchFund - Swapland agent",
    port=8012,
    seed=SWAPLAND_SEED,
    mailbox = True,
    #readme_path = "README_cryptonews.md",
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
            prompt = f"Try to identify user input and return it in output schema . This is user input: {item.text}."
            await ctx.send(
                AI_AGENT_ADDRESS,
                StructuredOutputPrompt(
                    prompt=prompt, output_schema=SwaplandRequest.schema()
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
        swapland_request = SwaplandRequest.parse_obj(msg.output)
        bl = swapland_request.blockchain
        sn = swapland_request.signal
        am = swapland_request.amount
        pk = swapland_request.private_key

        if not (bl and sn and am and pk):
            await ctx.send(session_sender,create_text_chat("Sorry, I couldn't find a valid query for the swapland agent. Please, enter a matching SwaplandRequest schema, including blockchain name, signal, amount and a private key."),)
            return
        #str(cn)
        
        #run a function!
        #response_text= str(get_recent_crypto_news(cryptonews_request.keywords))
        #search("Sell", "2177jhbekh271giuf3", "base", 0.0005) # test

        await ctx.send(session_sender, create_text_chat(response_text))
        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't process your request. Please try again later."
            ),
        )
        return



#USERINPUT_ADDRESS="agent1q2aczah05l97w8mnen2lcc59y052w8mphzwgv0q37npm9fml2fz5sw2s4vz"
#DISPATCHER_ADDRESS="agent1qw7k3cfqnexa08a3wwuggznd3cduuse469uz7kja6ugn85erdjnsqc7ap9a"



@proto.on_message(model=SwaplandRequest)
async def handle_message(ctx: Context, sender: str, msg: SwaplandRequest):
    """Handle incoming messages"""
    try:
        amount_to_swap = msg.amount
        private_key = msg.private_key
        signal = msg.signal
        network = msg.blockchain
        
        logger.info(f"Processed response: {msg}")
        
        #rp = SwaplandResponse(status = "Request to Swapland Agent sent.")
        #await ctx.send(sender,rp)
        
        await search(ctx,sender,msg) #debug to be enabled
    
    except Exception as e:
        txt=f"Error when processing the request: {e}"
        logger.error(txt)
        rp = SwaplandResponse(status = txt)
        await ctx.send(sender,rp)


async def search(ctx : Context, sender : str, msg: SwaplandRequest):
    # Search for agents matching the query
    # API endpoint and payload
    logger.info(f"Received signal: {msg.signal}")

    api_url = "https://agentverse.ai/v1/search/agents"
    query = "tag:fetchfundswapland"
    payload = {
        "search_text": str(query),#'<query>', tag:{tagid} tag:swaplandbaseethusdc
        "sort": "relevancy",
        "direction": "asc",
        "offset": 0,
        "limit": 5,
    }

    # Make a POST request to the API
    discovery = requests.post(api_url, json=payload)

    # Check if the request was successful
    if discovery.status_code == 200:
        # Parse the JSON response
        data = discovery.json()
        agents = data.get("agents", [])
        logger.info("Formatted API Response:")
        
        promptmsg= '''Agents discovered..
        
        '''
        prompt = f'''        
        These are all agents found through the search agent function tagged as swapland.
        Each agent has 3 parameters to consider: name, address and readme. Evaluate them all.
        You are looking for an agent that would execute a {msg.signal} signal on {msg.blockchain} network.
        Your response should be formatted as an agent address only, which can be found under the agent name.
        '''
        logger.info("Agents discovered..")
        for agent in agents:
            print("-" * 100)
            print("Agent Name:", agent.get("name"))
            print("Agent Address:", agent.get("address"))
            print("Readme:", agent.get("readme"))
            
            tmp = f'''
            Agent Name: {agent.get("name")}
            Agent Address: {agent.get("address")}
            Readme: {agent.get("readme")}
            
            
            
            '''
            
            prompt += tmp
            promptmsg += tmp
        
        
        rp = SwaplandResponse(status = str(promptmsg))
        await ctx.send(sender,rp)
            
        logger.info("Request sent to ASI1 model to evaluate the list of discovered agents..")
        
        response = query_llm(prompt)  # Query the AI for a decision
                
        logger.info(f"Agent address discovered: {response}")
        
        rpl = f"Search engine has found the agent for swap: {response}."
        rp = SwaplandResponse(status = rpl)
        await ctx.send(sender,rp)
        
        try:
            #pass
            #await call_swap(ctx, sender, msg, str(response)) # further execution!
            await ctx.send(response,msg) #swap execution
        except Exception as e:
            rpl = f"Error calling for swap: {e}"
            logger.error(msg)
            rp = SwaplandResponse(status = rpl)
            await ctx.send(sender,rp)
            
        logger.info("Program completed")
    else:
        logger.info(f"Request failed with status code {response.status_code}")

    return {"status": "Agent searched"}



agent2.include(chat_proto, publish_manifest=True)
agent2.include(struct_output_client_proto, publish_manifest=True)
agent2.include(proto, publish_manifest=True)


if __name__ == '__main__':
    agent2.run()
