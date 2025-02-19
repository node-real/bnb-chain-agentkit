# BNB Chain Langchain Extension Examples - Chatbot

This example demonstrates an agent setup as a terminal style chatbot with access to the full set of BNB Chain actions.

## Requirements
- Python 3.12+
- Uv for package management and tooling
  - [Uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/)
- [OpenAI API Key](https://platform.openai.com/docs/quickstart#create-and-export-an-api-key)

## Installation
```bash
uv venv --python 3.12
source .venv/bin/activate

uv sync
```

TODO: As of 2025-02-07, the `bnb-chain-agentkit` package is not published to PyPI. So you need to install it from source.

```bash
uv pip install -e ../.. # the root of the repo
```

## Run the Chatbot

### Set ENV Vars
- Ensure the following ENV Vars are set:
  - PRIVATE_KEY
  - BSC_PROVIDER_URL
  - OPBNB_PROVIDER_URL
  - OPENAI_API_KEY
  - BSCSCAN_API_KEY (optional)

```bash
uv run ./chatbot_async.py
```
