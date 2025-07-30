# FetchFund - AI-Powered Crypto Management Fund

A web application that leverages Fetch.ai agents to analyze cryptocurrency market conditions, provide trading recommendations, and execute it. 

Updated with ChatProtocol on FetchAI

## Features

- User input form to customize trading parameters
- Real-time market data and sentiment analysis
- AI-powered trading recommendations (BUY/SELL/HOLD)
- Transaction history tracking
- Multi-agent architecture for comprehensive analysis


## Requirements

- Python 3.12
- Fetch.ai uAgents package and other Python dependencies
- API keys (stored in .env)

## Agent Architecture

The system uses multiple agents for analysis:

- Main Agent: Coordinates all other agents
- Heartbeat Agent: Monitors user sentiment
- Coin Information Agent: Provides market data
- Fear & Greed Index Agent: Market sentiment analysis
- Crypto News Agent: Aggregates news articles
- LLM Agent: Uses AI to analyze data
- Reward Agent: Handles transactions
- Topup Agent: Manages wallet balances
- Swap Agents: Execute cryptocurrency trades
