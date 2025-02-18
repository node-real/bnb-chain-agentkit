# bnb_chain_agentkit/actions/token_price.py
import requests
from pydantic import BaseModel, Field
from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider

# Mapping from common token symbols to Coingecko IDs.
TOKEN_CG_IDS = {
    "BNB": "binancecoin",
    "BUSD": "binance-usd",
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDC": "usd-coin",
    "DAI": "dai",
    "USDT": "tether",
}

class TokenPriceQueryInput(BaseModel):
    token: str = Field(..., description="Token symbol (e.g., BNB, BUSD, BTC, ETH) or a Coingecko token id.")
    vs_currency: str = Field("usd", description="The fiat currency to compare against (default 'usd').")

def token_price_query(provider: BnbChainProvider, token: str, vs_currency: str = "usd") -> str:
    token_id = TOKEN_CG_IDS.get(token.upper(), token.lower())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies={vs_currency}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return f"Error fetching price: HTTP {response.status_code}"
        data = response.json()
        if token_id not in data:
            return f"Token '{token}' not found in Coingecko API."
        price = data[token_id].get(vs_currency)
        return f"The current price of {token.upper()} is {price} {vs_currency.upper()}."
    except Exception as e:
        return f"Error fetching token price: {str(e)}"

class TokenPriceQueryAction(BnbChainAction):
    name: str = "token_price_query"
    description: str = "Fetch the current price of a token using the Coingecko API."
    args_schema: type[BaseModel] = TokenPriceQueryInput
    func = token_price_query
