## BNB-chain-agentkit

This is a Langchain extension for BNB Chain.

This toolkit equips LLM agents with the ability to interact with BNB Chain and execute on-chain operations, including getting balances, transferring tokens, swapping tokens, staking, bridging, and deploying different types of ERC tokens.

## Setup

### Prerequisites

- Python 3.12+

### Installation

```bash
pip install bnb-chain-agentkit
```

### Environment Variables

```bash
cp .env.example .env
```

- `PRIVATE_KEY`: Your private key for the BNB Chain account.
- `BSC_PROVIDER_URL`: The URL of the BNB Smart Chain provider.
- `OPBNB_PROVIDER_URL`: The URL of the Optimism BNB Smart Chain provider.

You can set your own RPC endpoint or use a public one listed here: [https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/](https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/)

## Usage

### Basic Setup

```python
from bnb_chain_agentkit.agent_toolkits import BnbChainToolkit
from bnb_chain_agentkit.utils import BnbChainAPIWrapper

# Configure BNB Chain Langchain Extension.
bnb_chain = BnbChainAPIWrapper()

# Initialize BNB Chain Toolkit and get tools.
bnb_chain_toolkit = BnbChainToolkit.from_bnb_chain_api_wrapper(bnb_chain)
```

View available tools:
```python
tools = bnb_chain_toolkit.get_tools()
print('Supported tools:')
for tool in tools:
    print(tool.name)
```

The toolkit provides the following tools:

1. **get_balance** - Get balance for a specific token of given account
2. **transfer** - Transfer tokens to a specific address
3. **faucet** - Request test tokens from faucet
4. **swap** - Swap tokens on PancakeSwap
5. **stake** - Stake BNB to ListaDao
6. **bridge** - Bridge tokens between BSC and opBNB
7. **deploy** - Deploy a new ERC20/ERC7721/ERC1155 token

### Using with an Agent

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# Get tools and create agent
tools = bnb_chain_toolkit.get_tools()
agent_executor = create_react_agent(llm, tools)

# Example usage
events = agent_executor.stream(
    {"messages": [("user", "Check BNB balance of 0x1234")]},
    stream_mode="values"
)

for event in events:
    event["messages"][-1].pretty_print()
```

Expected output:
```
================================ Human Message =================================

Check my BNB balance
================================== Ai Message ==================================
Tool Calls:
get_balance (call_w4HfhOLX9d5lH7emf1QKQCF4)
Call ID: call_w4HfhOLX9d5lH7emf1QKQCF4
Args:
    account: 0x1234
    token: BNB
================================= Tool Message =================================
Name: get_balance

Balances for account 0x1234 of BNB:
6145615640500000000 (decimals: 18)
================================== Ai Message ==================================

Your BNB balance is 6.1456156405 BNB.
```

Please refer to `examples/chatbot` for more detailed usage.

## Credits

Special thanks to [CDP (Coinbase Developer Platform)](https://github.com/coinbase/agentkit.git). The architecture and implementation patterns of this toolkit were inspired by their excellent work in building AI agent.
