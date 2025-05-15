
![domain:innovation-lab](https://img.shields.io/badge/innovation--lab-3D8BD3)
![domain:fetchfund](https://img.shields.io/badge/fetchfund-3D23DD)
![tag:fetchfundswapland](https://img.shields.io/badge/fetchfundswapland-4648A3)


# Agent Description
#### Role: 
FetchFund - Buy signal on Base. Executes Buy signal on Base network. USDC-to-ETH swaps on Base.
Workflow: Awaits requests from the Swapfinder Agent. Performs the swap using the provided wallet
address and private key. Returns a success status to the Main Agent.



#### Workflow:
Buy ETH signal. Fetchfund agent which uses uniswapV2 smart contract to BUY ETH (swap USDC into ETH)
on base network.
