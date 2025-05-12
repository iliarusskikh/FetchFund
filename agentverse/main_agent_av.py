

import logging
import sys
import os
#from dotenv import load_dotenv
import atexit
import time
from uagents import Agent, Context, Model, Field
from typing import Optional
#from asi.llm_agent import query_llm

from uagents.network import wait_for_tx_to_complete
from uagents.setup import fund_agent_if_low

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address

from uagents.network import get_faucet, get_ledger
from uagents.agent import AgentRepresentation #to use txn wallet
from uagents.config import TESTNET_REGISTRATION_FEE

from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.wallet import LocalWallet

import asyncio
import json


#ask for chain the user would like to watch and add to variable chain
#based on the choise base, ether, or polygon, choose or discover appropriate coin info agent.

#ASI1_API_KEY = os.getenv("ASI1_API_KEY")
#NEWS_API_KEY = os.getenv("NEWS_API_KEY")
#CMC_API_KEY = os.getenv("CMC_API_KEY")
#load_dotenv()

METAMASK_PRIVATE_KEY = os.getenv("METAMASK_PRIVATE_KEY")
AGENTVERSE_API_KEY = os.getenv("AGENTVERSE_API_KEY")




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

# Agentverse agent addresses - Updated to match actual running agents
HEARTBEAT_AGENT="agent1q20850rnurygmuuu5v3ryzhxl2mrfnwler8gzc0h4u4xp4xxuruljj54rwp"
TOPUP_AGENT="agent1q08e85r72ywlp833e3gyvlvyu8v7h7d98l97xue8wkcurzk282r77sumaj7"
REWARD_AGENT="agent1qgywfpwj62l0jkwtwrqly8f3mz5j7qhxhz74ngf2h8pmagu3k282scgzpmj"
COIN_AGENT="agent1qthmuhfu5xlu4s8uwlq7z2ghxhpdqpj2r8smaushxu0qr3k3zcwuxu87t0t"
CRYPTONEWS_AGENT="agent1qgy6eh453lucsvgg30fffd70umcq6fwt2wgx9ksyfxnw45wu4ravs26rvt6"
FGI_AGENT="agent1q2ecqwzeevp5dkqye98rned02guyfzdretw5urh477pnmt6vja4psnu3esh"#"agent1qfyrgg8w5pln25a6hcu3a3rx534lhs32aryqr5gx08djdclakzuex98dwzn" mailbox
REASON_AGENT="agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c" #ASI:One


SWAPLAND_AGENT="agent1qdcpchwle7a5l5q5le0xkswnx4p78jflsnw7tpchjz0dsr2yswepqdvk7at"


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

### COININFO AGENT ###
class BlockchainRequest(Model):
    blockchain: str = Field(
        description="Blockchain or crypto network name to check the price of its native coin",
    )

class CoinResponse(Model):
    name: str
    symbol: str
    current_price: float
    market_cap: float
    total_volume: float
    price_change_24h: float

### CRYPTONEWS AGENT ###
class CryptonewsRequest(Model):
    limit: Optional[int] = 1
    keywords: str = Field(
        description="user's keywords for news query"
    )

class CryptonewsResponse(Model):
    response: str

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
    
### REASON AGENT ASI:ONE ###
class ContextPrompt(Model):
    context: str
    text: str
    
class Response(Model):
    text: str
    
class ASI1Request(Model):
    query: str
    
class ASI1Response(Model):
    decision: str


### REWARD AGENT ###
class PaymentRequest(Model):
    wallet_address: str
    amount: int
    denom: str
 
class TransactionInfo(Model):
    tx_hash: str

class PaymentInquiry(Model):
    ready: str
    
class PaymentReceived(Model):
    status: str
    
class RewardRequest(Model):
    status: str = Field(
        description="user requesting reward",
    )
    
### TOP-UP AGENT ###
class TopupRequest(Model):
    amount: float
    agentwallet: str
    fetwallet: str

class TopupResponse(Model):
    status: str
    
### SWAPFINDER AGENT ###
class SwaplandRequest(Model):
    blockchain: str
    signal: str
    amount: float
    private_key: str

class SwaplandResponse(Model):
    status: str
    
### SWAP AGENT ###
class SwapCompleted(Model):
    status: str
    message: str
###--------------###


### USER_INPUTS ###
USERINPUT_ASIWALLET_PRIVATEKEY = ""
USERINPUT_EVMWALLET_PRIVATEKEY = ""
USERINPUT_HBDATA= ""
USERINPUT_NETWORK= ""
USERINPUT_RISKSTRATEGY= ""
USERINPUT_INVESTORTYPE= ""
USERINPUT_REASON= ""
USERINPUT_AMOUNT_TOPUP= ""
USERINPUT_NEWS_KEYWORDS= ""

###--------------###


ONETESTFET = 1000000000000000000
REWARD = 2000000000000000000 #expected to receive
DENOM = "atestfet"

NETWORK = "base" #default global
COININFORMATION = ""
CRYPTONEWSINFO = ""

ASIITERATIONS = 4
RISK = " "
INVESTOR = " "
FGIOUTPUT = " "
USERREASON = ""

# Global variable to store analysis results
LATEST_ANALYSIS = {
    "action": "",
    "amount": 0.0,
    "price": 0.0,
    "details": "",
    "timestamp": 0.0
}

# Initialize the agent
agent = Agent()


# Add a new model for API wrapper requests
class ApiWrapperRequest(Model):
    network: str
    investor_type: str
    risk_strategy: str
    reason: str
    timestamp: float

# Response model for analysis results
class AnalysisResult(Model):
    action: str
    amount: float
    price: float
    details: str
    timestamp: float

# Add models for API agent communication
class TradingRequest(Model):
    network: str
    investor_type: str
    risk_strategy: str
    reason: str
    timestamp: float
    request_id: str

class TradingResponse(Model):
    action: str
    amount: float
    price: float
    details: str
    timestamp: float
    request_id: str
    
    

@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    """Logs agent startup details."""
    logging.info(f"✅ Agent started: {ctx.agent.address}")
    ctx.logger.info(f"Hello! I'm {agent.name} and my address is {agent.address}, my wallet address {agent.wallet.address()}")
    ledger: LedgerClient = get_ledger()
    agent_balance = ledger.query_bank_balance(Address(agent.wallet.address()))/ONETESTFET
    ctx.logger.info(f"My balance is {agent_balance} TESTFET")




#START OF FRONTEND INTEGRATION

#create an agent which would send all required inputs via agent which uses mailbox
#first launch command
# Handler for incoming API agent requests
@agent.on_message(model=TradingRequest)
async def handle_trading_request(ctx: Context, sender: str, msg: TradingRequest):
    """Handle trading requests from the API agent"""
    ctx.logger.info(f"Received trading request from {sender}: {msg.request_id}")
    
    # Extract the trading parameters
    global NETWORK, RISK, INVESTOR, USERREASON
    NETWORK = msg.network
    INVESTOR = msg.investor_type
    RISK = msg.risk_strategy
    USERREASON = msg.reason
    
    # In a real implementation, you'd trigger the full analysis flow here
    # by communicating with all the needed agents (coin_info, fgi, news, llm, etc.)
    # For now, we'll provide a simulated response based on simple rules
    
    # Simplified logic - in real use, this would be based on comprehensive analysis
    action = "BUY" if NETWORK == "ethereum" else "SELL"
    action = "HOLD" if "hold" in USERREASON.lower() else action
    
    # If the user explicitly mentions an action in their reason, use that
    if "buy" in USERREASON.lower():
        action = "BUY"
    elif "sell" in USERREASON.lower():
        action = "SELL"
    
    # Send the analysis result back to the API agent
    await ctx.send(
        sender,
        TradingResponse(
            action=action,
            amount=0.5,
            price=2000.00,
            details=f"Analysis complete based on {RISK} strategy for {INVESTOR} investor on {NETWORK}.",
            timestamp=msg.timestamp,
            request_id=msg.request_id
        )
    )
    
    # Store the result locally as well
    global LATEST_ANALYSIS
    LATEST_ANALYSIS = {
        "action": action,
        "amount": 0.5,
        "price": 2000.00,
        "details": f"Analysis complete based on {RISK} strategy for {INVESTOR} investor on {NETWORK}.",
        "timestamp": msg.timestamp
    }

#END OF FRONTEND INTEGRATION












#@agent.on_interval(period=24 * 60 * 60.0)  # Runs every 24 hours
async def swapland_request(ctx: Context):
    """Confirm that the user is calm and not overexcited"""
    
    #await asyncio.sleep(15)
    time.sleep(30)
    #need to check the heartbeat data
    try:
        data12 = [
            {"dateTime": "2025-04-25T20:37:15", "value": {"bpm": 122, "confidence": 3}},
            {"dateTime": "2025-04-25T20:37:15", "value": {"bpm": 74, "confidence": 3}},
            {"dateTime": "2025-04-25T20:37:15", "value": {"bpm": 70, "confidence": 2}},
            {"dateTime": "2025-04-25T20:37:15", "value": {"bpm": 75, "confidence": 0}}
        ]

        await ctx.send(HEARTBEAT_AGENT,HeartbeatRequest(hbdata=str(data12)))

    except Exception as e:
        agent._logger.info(f"Error sending data to agent: {e}")
    
    
    #await ctx.send(HEARTBEAT_AGENT, HeartbeatRequest(status="ready"))
    


# Waits for completion of heartbeat agent.
@agent.on_message(model=HeartbeatResponse)
async def message_handler(ctx: Context, sender: str, msg: HeartbeatResponse):
    if (msg.status == "continue"):
        ctx.logger.info(f"Received response{msg.status}. Lets trade")
        
        #execute topup_agent to receive funds
        #user input required
        topupamount = 10
        if (topupwallet > 0):#if 0 then top up not required
            #user input required
            topupamount = 10#input("How many FET to transfer over?: ").lower()#convert from string to float
            
            fetchwall= (str)(agent.wallet.address())
            await ctx.send(TOPUP_AGENT, TopupRequest(amount=topupamount, agentwallet=fetchwall, fetwallet="empty"))
        else:
            #execute reward_agent to pay fees for using swapland service. this might not be async though
            try:
                await ctx.send(REWARD_AGENT, PaymentInquiry(ready = "ready"))
                ctx.logger.info(f"Ready to pay status sent")
            except Exception as e:
                logging.error(f"Failed to send request to reward_Agent to pay fees for using swapland services: {e}")

    else:
        ctx.logger.info(f"Canceling the process..: {msg.status}")
        



#main agent received requested funds
@agent.on_message(model=TopupResponse)
async def response_funds(ctx: Context, sender: str, msg: TopupResponse):
    """Handles topup response."""
    logging.info(f"📩 User's wallet topped up: {msg.status}")
    #execute reward_agent to pay fees for using swapland service. this might not be async though
    #await asyncio.sleep(5)
    ledger: LedgerClient = get_ledger()
    agent_balance = ledger.query_bank_balance(Address(agent.wallet.address()))/ONETESTFET
    #print(f"Balance after fees: {agent_balance} TESTFET")
    ctx.logger.info(f"Balance after topup wallet: {agent_balance} TESTFET")
    
    try:
        
        await ctx.send(REWARD_AGENT, PaymentInquiry(ready = "ready"))
        ctx.logger.info(f"Ready to pay status sent")
    except Exception as e:
        logging.error(f"Failed to send request to reward_Agent to pay fees for using swapland services: {e}")



#received request to make a payment for execution from reward_agent
@agent.on_message(model=PaymentRequest)
async def message_handler(ctx: Context, sender: str, msg: PaymentRequest):
    ctx.logger.info(f"Received message from {sender}: {msg}")
    
    #send the payment
    fees = msg.amount/ONETESTFET #input does not compile variables
    #logging.info(f"You are required to pay {fees} FET for this service. ")
    
    #need to add userinput
    rewardtopay = "yes"#input(f"You are required to pay {fees} FET for this service. Proceed?[yes/no]: ").lower()
    
    
    #instead i need to check here if the user agent has enough funds. if not, then return error, and finish the execution!
    
    
    if (rewardtopay == "yes"):
        transaction = ctx.ledger.send_tokens(msg.wallet_address, msg.amount, msg.denom,agent.wallet)
    else:
        exit(1)
    # send the tx hash so reward agent can confirm with fees payment
    await ctx.send(sender, TransactionInfo(tx_hash=transaction.tx_hash))#str(ctx.agent.address)


#confirmation from reward_agent after main agent paid fees for exection.
@agent.on_message(model=PaymentReceived)
async def message_handler(ctx: Context, sender: str, msg: PaymentReceived):
    if (msg.status == "success"):
        ctx.logger.info(f"Fees transaction successful!")
        ledger: LedgerClient = get_ledger()
        agent_balance = ledger.query_bank_balance(Address(agent.wallet.address()))/ONETESTFET
        ctx.logger.info(f"Balance after fees: {agent_balance} TESTFET")
        
        
        #startup asi1 routine
        """Requests market data for the monitored coin once a day."""
        try:
            # Confirm chain
            global NETWORK
            #print(f"Please, confirm the chain to request the data from")
            
            #need to add userinput
            NETWORK = "base"#input("Blockchain [ethereum/base/bitcoin/matic-network]? ").lower()
            
            
            if ((NETWORK != "base") and (NETWORK != "ethereum") and (NETWORK != "matic-network") and (NETWORK != "bitcoin")):
                print("Aborted")
                sys.exit(1)
            
            await asyncio.sleep(5)
            
            await ctx.send(COIN_AGENT, BlockchainRequest(blockchain=NETWORK))
            print(f"Sent request") #stuck here

        except Exception as e:
            logging.error(f"Failed to send request: {e}")
        
    else:
        ctx.logger.info(f"Fees transaction unsuccessful!")
        

@agent.on_message(model=CoinResponse)
async def handle_coin_response(ctx: Context, sender: str, msg: CoinResponse):
    """Handles coin market data and requests Cryptonews."""
    logging.info(f"📩 Received CoinResponse: {msg}")
    
    global COININFORMATION
    
    COININFORMATION = msg
    try:
        #temporary disabled cryptonews
        #await ctx.send(FGI_AGENT, FGIRequest()) #temporary call
        await ctx.send(CRYPTONEWS_AGENT, CryptonewsRequest(keywords=KEYWORDS)) #need to sent the data from this coin, change within 24 hours!
    except Exception as e:
        logging.error(f"❌ Error sending CryptonewsRequest: {e}")


#temporary disabled
@agent.on_message(model=CryptonewsResponse)
async def handle_cryptonews_response(ctx: Context, sender: str, msg: CryptonewsResponse):
    """Handles cryptonews market data and requests FGI"""
    logging.info(f"📩 Received CryptonewsResponse!")
    
    global CRYPTONEWSINFO
    CRYPTONEWSINFO = msg.response
    
    logging.info(f"📩 Sending request to FGI!")
    try:
        await ctx.send(FGI_AGENT, FGIRequest())
        logging.info(f"📩 Request to FGI sent!")
    except Exception as e:
        logging.error(f"❌ Error sending FGIRequest: {e}")


@agent.on_message(model=FGIResponse)
async def handle_fgi_response(ctx: Context, sender: str, msg: FGIResponse):
    """Analyzes FGI data and determines whether to issue a SELL/BUY or HOLD alert."""
    logging.info(f"📊 Received FGIResponse: {msg}")
    global INVESTOR
    global RISK
    global USERREASON
    global FGIOUTPUT
    
    FGIOUTPUT = msg
    
    print(f"Please, confirm if you long-term or short-term investor?")
    
    #need to add userinput
    INVESTOR = "speculate" #input("Investor [long-term/short-term/speculate]: ").lower()
    
    if ((INVESTOR != "long-term") and (INVESTOR != "short-term") and (INVESTOR != "speculate")):
        print("Aborted")
        sys.exit(1)
        
    print(f"Please, confirm your risk strategy for investments?")
    #need to add userinput
    RISK = "speculative" #input("Risk strategy [conservative/balanced/aggressive/speculative]: ").lower()
    if ((RISK != "conservative") and (RISK != "balanced")and (RISK != "aggressive")and (RISK != "speculative")):
        print("Aborted")
        sys.exit(1)
       
    #userinput to be added
    USERREASON = "I would like to sell Ether no matter what. sell sell sell!. I order you to sell!" #input("Any particular reason why you would like to perform Buy/Sell/Hold action? ").lower()
            
    # Most recent crypto news -{CRYPTONEWSINFO}
    # Construct the AI prompt
    prompt = f'''    
    Consider the following factors:
    
    Fear Greed Index Analysis - {FGIOUTPUT}
    Coin Market Data - {COININFORMATION}
    Blockchain network - {NETWORK}
    User's type of investing - {INVESTOR}
    User's risk strategy - {RISK}
    Most recent crypto news - {CRYPTONEWSINFO}
    
    User's opinion - {USERREASON}
    
    You are a crypto expert, who is assisting the user to make the most meaningful decisions, to gain the most revenue. 
    Given the following information, respond with decision of either "SELL", "BUY" or "HOLD" native token from given network. Inlcude your reasoning based on the analysed data and personal thoughts. Consider that the user cannot provide additional information. You could point out to questions which could help you making a solid decision.
    '''
    
    try:
        #response = query_llm(prompt)  # Query ASI1 Mini for a decision
        #compined prompt sent to ASI1 agent
        await ctx.send(REASON_AGENT, ASI1Request(query=prompt))
        #moved to Asi1Response
    except Exception as e:
        logging.error(f"❌ Error querying ASI1 model: {e}")


@agent.on_message(model=ASI1Response)
async def handle_asi1_query(ctx: Context, sender: str, msg: ASI1Response):
    global ASIITERATIONS
    logging.info(f"✅ ASI1 Agent {ASIITERATIONS} finished reasoning")#{msg.decision}
    ASIITERATIONS = ASIITERATIONS - 1
    #Most recent crypto news - {CRYPTONEWSINFO}
    if(ASIITERATIONS > 1):
        prompt = f'''    
        Consider the following factors:
        
        Fear Greed Index Analysis - {FGIOUTPUT}
        Coin Market Data - {COININFORMATION}
        Blockchain network - {NETWORK}
        User's type of investing - {INVESTOR}
        User's risk strategy - {RISK}
        Most recent crypto news - {CRYPTONEWSINFO}
        
        User's opinion - {USERREASON}
        
        You are a crypto expert, who is assisting the user to make the most meaningful decisions, to gain the most revenue. 
        
        This query has been analysed with the following reasoning:
        "{msg.decision}"
        
        Given the following information and reasoning from other expert, respond with decision of either "SELL", "BUY" or "HOLD" native token from {NETWORK} network. Inlcude all of the reasoning based on the analysed data and personal thoughts. Consider that the information provided is the only input from the user, and the user cannot provide additional information. However, you could point out to the area or questions which could help you making a solid decision.
        '''
        await ctx.send(REASON_AGENT, ASI1Request(query=prompt))

    #Most recent crypto news - {CRYPTONEWSINFO}
    if(ASIITERATIONS == 1):
        prompt = f'''    
        Consider the following factors:
        
        Fear Greed Index Analysis - {FGIOUTPUT}
        Coin Market Data - {COININFORMATION}
        Blockchain network - {NETWORK}
        User's type of investing - {INVESTOR}
        User's risk strategy - {RISK}
        Most recent crypto news - {CRYPTONEWSINFO}        
        
        User's opinion - {USERREASON}   
        
        You are an independent expert of a crypto market with knowledge of how worldwide politis affects the cryptomarket. You are assisting the user to make the most meaningful decisions, to gain the most revenue whilst minimising potential losses. 
        
        This query has been analysed by {ASIITERATIONS} other crypto experts, and here is a summery of their reasoning:
        "{msg.decision}"
        
        "SELL" means swapping native crypto coin into USDC.
        "BUY" means swapping USDC into native crypto coin.
        "HOLD" means no actions.
        
        Given the following information and reasoning from other expert responses, make a decision by responding ONLY with one word "SELL", "BUY" or "HOLD" for a native token from given network. Again, your output is ether "SELL", "BUY" or "HOLD". 
        '''
        await ctx.send(REASON_AGENT, ASI1Request(query=prompt))
    
    amountt = 0;
    if (ASIITERATIONS == 0):
        if (("SELL" in msg.decision) or ("BUY" in msg.decision)):
                # i need to insert this after reason_agent(ASI1 llm) is done.
            try:
                signall=""
                
                if "BUY" in msg.decision:
                    logging.critical("🚨 BUY SIGNAL DETECTED!")
                    signall = "tag:fetchfundbaseusdceth"#Buy ETH signal. Convert USDC to ETH
                    amountt = 0.1 #usdc to eth
                elif "SELL" in msg.decision:
                    logging.critical("✅ SELL SIGNAL DETECTED!")
                    #make signal a tag, so that a search query is constructed here "swaplandusdctoeth", then add this to search( ... )
                    signall = "tag:fetchfundbaseethusdc"
                    amountt = 0.00007 #ETH to USDC
                
                chain = NETWORK
                
                await ctx.send(SWAPLAND_AGENT, SwaplandRequest(blockchain=chain,signal=signall, amount = amountt, private_key = METAMASK_PRIVATE_KEY))

            except Exception as e:
                logging.error(f"Failed to send request: {e}")
        else:
            logging.info("⏳ HOLD decision received.")
            print("HOLD")
            try:
                await ctx.send(REWARD_AGENT, RewardRequest(status="reward"))
            except Exception as e:
                logging.error(f"Failed to send request for reward: {e}")
            
            #exit(1)
    

# Handle incoming messages with the SwaplandResponse model from ai agent swapfinder_agent
@agent.on_message(model=SwaplandResponse)
async def message_handler(ctx: Context, sender: str, msg: SwaplandResponse):
    ctx.logger.info(f"Received message from {sender}: {msg.status}")














# Waits for completion of swapland agents. then executes request for reward from reward_agent
@agent.on_message(model=SwapCompleted)
async def message_handler(ctx: Context, sender: str, msg: SwapCompleted):
    if (msg.status == "swapcompleted"):
        ctx.logger.info(f"{msg.message}")
        
        try:
            await ctx.send(REWARD_AGENT, RewardRequest(status="reward"))
        except Exception as e:
            logging.error(f"Failed to send request for reward: {e}")
    
    else:
        ctx.logger.info(f"Fail to execute swap via swapland: {msg.status}")
        
        
#confirmation that reward has been received from reward_agent
@agent.on_message(model=TransactionInfo)
async def confirm_transaction(ctx: Context, sender: str, msg: TransactionInfo):
    ctx.logger.info(f"Received transaction info from {sender}: {msg}")
    tx_resp = await wait_for_tx_to_complete(msg.tx_hash, ctx.ledger)
 
    coin_received = tx_resp.events["coin_received"]
    if (
            coin_received["receiver"] == str(agent.wallet.address())
            and coin_received["amount"] == f"{REWARD}{DENOM}"
    ):
        ctx.logger.info(f"Reward transaction was successful: {coin_received}")
    else:
        ctx.logger.info(f"Transaction was unsuccessful: {coin_received}")

    ledger: LedgerClient = get_ledger()
    agent_balance = (ledger.query_bank_balance(Address(agent.wallet.address())))/ONETESTFET
    ctx.logger.info(f"Balance after receiving reward: {agent_balance} TESTFET")
    
    await ctx.send(sender,PaymentReceived(status="reward"))#str(ctx.agent.address)



# Ensure the agent starts running
if __name__ == "__main__":
    agent.run()
