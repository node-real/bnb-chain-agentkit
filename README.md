- [📖 BNB Chain Agentkit](#-bnb-chain-agentkit)
- [🗂 Repository Structure](#-repository-structure)
- [🚀 Quickstart](#-quickstart)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
- [Usage](#usage)
  - [Basic Setup](#basic-setup)
  - [Using with an Agent](#using-with-an-agent)
  - [Example interactions when using the examples/chatbot](#example-interactions-when-using-the-exampleschatbot)
- [📝 License](#-license)
- [🔒 Legal and Privacy](#-legal-and-privacy)
- [Credits](#credits)


## 📖 BNB Chain Agentkit

This is a Langchain extension for BNB Chain.

This toolkit equips LLM agents with the ability to interact with BNB Chain and execute on-chain operations, including getting balances, transferring tokens, swapping tokens, staking, bridging, and deploying different types of ERC tokens.



## 🗂 Repository Structure
BNB Chain Agentkit contains a kit package and example package.

```
bnb-chain-agentkit
├── README.md
├── bnb_chain_agentkit
│   ├── actions
│   ├── agent_toolkits
│   ├── provider
│   ├── tools
│   └── utils
├── examples
│   └── chatbot
│       ├── README.md
│       ├── chatbot_async.py
│       └── pyproject.toml
├── pyproject.toml
```


## 🚀 Quickstart

### Prerequisites

- [Python 3.12+](https://www.python.org/downloads/) 
- [OpenAI API Key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key)

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
- `OPENAI_API_KEY`: The open api key used to interact with chatgpt.

You can set your own RPC endpoint or use a public one listed here: [https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/](https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/)



## Usage
A full example is put in bnb-chain-agentkit/examples/chatbot folder

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
7. **deploy** - Deploy a new ERC20/ERC7721/ERC1155 token on both BSC and opBNB

### Using with an Agent

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o")

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

### Example interactions when using the examples/chatbot 


- Check my BNB balance   
    **User**: `get my BNB balance`   
    **Chatbot**: `Your BNB balance is approximately 0.0838 BNB.`

- Request test coin from faucet  
    **User**: `Request BNB from the BNB Chain official faucet`  
    **Chatbot**: `Successfully requested BNB for 0x123. Transaction hash: 0x456`
 

- Bridge  
    **User**: `Bridge 0.0001 BNB from BSC to opBNB`  
    **Chatbot**: `Successfully bridged 0.0001 BNB from BSC to opBNB. You can view the transaction with hash [0xc7c1a38d6c3cfc7cc379ae326ae771062e0e436963f28fac9b6ee2580d6d4c44](https://bscscan.com/tx/0xc7c1a38d6c3cfc7cc379ae326ae771062e0e436963f28fac9b6ee2580d6d4c44).`


    More examples about bridge:
    1. Deposit 0.0001 BNB from BSC to opBNB
    2. Withdraw 0.0001 BNB from opBNB to BSC
    3. Deposit 0.1 0x123 token from BSC to address 0x123 on opBNB. The corresponding token address on opBNB is 0x123


- Deploy an ERC20 token  
    **User**: `deploy an ERC20 token with name 'ClydePepper', symbol ClydePepper, decimals 18, total supply 10000 on BSC`  
    **Chatbot**: `The ERC20 token 'ClydePepper' has been successfully deployed on the BSC chain with the contract address: [0x123](https://bscscan.com/address/0x123).`
    
    More user input examples about smart contracts deployment:
    1. `Deploy an ERC1155 contract , baseURI 'https://my-1155peter-base-uri.com'`
    2. `Deploy an ERC721 NFT contract with name 'PitterNFT', symbol 'PitterNFT', baseURI 'https://my-nft-peter-uri.com' on opbnb`

- Transfer  
    **User**: `Transfer 0.0001 BNB to 0x123`  
    **Chatbot**: `Successfully transferred 0.0001 BNB to the address [0x123](https://bscscan.com/address/0x123). You can view the transaction with hash [0x123](https://bscscan.com/tx/0x123).`
    
- Swap  
    You can do swap on pancakeswap by inputing examples as below :
    1. `Swap 0.0001 BNB for USDC on BSC`
    2. `Buy some token of 0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d using 0.01 USDT on BSC. The slippage should be no more than 5%`

- Stake  
    You can stake BNBs on ListaDao by inputting examples as below :
    1. `Stake 0.001 BNB on BSC`
    2. `Deposit 0.0001 BNB to Lista DAO on bsc`
    3. `Undelegate 0.01 BNB on BSC`
    4. `Claim unlocked BNB from Lista DAO on bsc`

Please refer to `examples/chatbot` for more detailed usage.

## 📝 License

The BNB Chain Agentkit is licensed under the [Apache-2.0](LICENSE.md) license.

## 🔒 Legal and Privacy
The BNB Chain Agentkit software is novel and experimental, and is therefore provided on an AS-IS basis. The software is intended to be used only for the purposes of assisting with designing blockchain transactions and enabling other API integrations using natural language inputs, and is not intended to provide (i) an offer, or solicitation of an offer, to invest in, or to buy or sell, any interests or shares, or to participate in any investment or trading strategy, (ii) accounting, legal, tax advice, investment recommendations or other professional advice or (iii) an official statement of Nodereal. Acts proposed or performed by an agent through this software are NOT acts of Nodereal. You should consult with a professional advisor before making any decisions based on the information provided by the software. You are not permitted to use the proceeds of loans or credit to purchase digital assets on or through Nodereal.com, Nodereal's APIs, the Nodereal mobile application, or any other Nodereal website or product, including AgentKit. No representation or warranty is made, expressed or implied, with respect to the accuracy, completeness, reliability, security, or suitability of the software or to any information provided in connection with the software. The risk of loss through use of the software can be substantial, and you assume any and all risks of loss and liability. The software may produce output that is inaccurate, incorrect, unpredictable or undesirable, and it is the user’s exclusive responsibility to evaluate the output and the use-case and determine whether it is appropriate. 

## Credits

Special thanks to [CDP (Coinbase Developer Platform)](https://github.com/coinbase/agentkit.git). The architecture and implementation patterns of this toolkit were inspired by their excellent work in building AI agent.
