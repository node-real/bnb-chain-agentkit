import logging
from collections.abc import Callable
from typing import Optional

from pydantic import BaseModel, Field
from web3 import Web3

from bnb_chain_agentkit.actions.abi import ERC20_ABI
from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider

logger = logging.getLogger(__name__)

GET_BALANCE_PROMPT = """
This tool retrieves the balance of a specified asset for a given account.

It takes the account address and the token contract address as inputs.

Important notes:
- The account address is optional. If not specified, the default account will be used.
- The token could be a valid token address or "BNB".
"""


class GetBalanceInput(BaseModel):
    """Input argument schema for get balance action."""

    account: Optional[str] = Field(
        None,
        description='The account address to get the balance for. Optional. Could be None or a valid ethereum address starting with "0x".',
    )
    token: str = Field(
        'BNB',
        description='The token to get the balance for, e.g. `BNB` or `0x...`.',
    )


def get_balance(provider: BnbChainProvider, account: Optional[str], token: str) -> str:
    """Get balance of a specified asset for a given account.

    Args:
        provider (BnbChainProvider): The provider to use for the query.
        account (Optional[str]): The account address to get the balance for. Optional. Could be None or a valid ethereum address starting with "0x".',
        token (str): The token to get the balance for, e.g. `BNB` or `0x...`.

    Returns:
        str: A message containing the balance information of the account for the given asset.
    """

    client = provider.get_current_client()
    address = Web3.to_checksum_address(account) if account else provider.get_address()

    if token == 'BNB':
        balance = client.eth.get_balance(address)  # type: ignore[arg-type]
        decimals = 18
        token_name = token
    else:
        token_address = Web3.to_checksum_address(token)
        contract = client.eth.contract(token_address, abi=ERC20_ABI)

        balance = contract.functions.balanceOf(address).call()
        decimals = contract.functions.decimals().call()
        token_name = contract.functions.name().call()

    return f'Balances for account {address} of {token_name}:\n{balance} (decimals: {decimals})'


class GetBalanceAction(BnbChainAction):
    """Get wallet balance action."""

    name: str = 'get_balance'
    description: str = GET_BALANCE_PROMPT
    args_schema: Optional[type[BaseModel]] = GetBalanceInput
    func: Optional[Callable[..., str]] = get_balance
