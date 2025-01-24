# BNB Chain Langchain Extension Examples - Chatbot

This example demonstrates an agent setup as a terminal style chatbot with access to the full set of BNB Chain actions.

## Requirements
- Python 3.12+
- [OpenAI API Key](https://platform.openai.com/docs/quickstart#create-and-export-an-api-key)

## Installation
```bash
pip install langchain-bnb-chain
```

## Run the Chatbot

### Set ENV Vars
- Ensure the following ENV Vars are set:
  - PRIVATE_KEY
  - BSC_PROVIDER_URL
  - OPBNB_PROVIDER_URL
  - OPENAI_API_KEY

```bash
python chatbot_async.py
```
