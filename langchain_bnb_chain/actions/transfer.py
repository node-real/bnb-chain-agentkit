import logging
from collections.abc import Callable
from typing import Optional

from pydantic import BaseModel, Field
from web3 import Web3

from langchain_bnb_chain.actions.abi import ERC20_ABI
from langchain_bnb_chain.actions.bnb_chain_action import BnbChainAction
from langchain_bnb_chain.actions.utils.uints import parse_uints
from langchain_bnb_chain.provider.bnb_chain_provider import BnbChainProvider

logger = logging.getLogger(__name__)

TRANSFER_PROMPT = """
This tool will transfer an asset from the wallet to another onchain address.

It takes the amount, token, and recipient as inputs.

Important notes:
- The token could be a valid token address or "BNB".
- Ensure sufficient balance of the input asset before transferring
- When sending native assets (e.g. 'BNB' on BSC mainnet), ensure there is sufficient balance for the transfer itself AND the gas cost of this transfer
"""


class TransferInput(BaseModel):
    """Input argument schema for transfer action."""

    amount: str = Field(description='The amount of the asset to transfer, e.g. `15`, `0.000001`')
    token: str = Field(
        'BNB',
        description='The token to transfer, e.g. `BNB` or `0x...`.',
    )
    recipient: str = Field(
        description='The recipient to transfer the funds, e.g. `0x58dBecc0894Ab4C24F98a0e684c989eD07e4e027`',
    )


def transfer(
    provider: BnbChainProvider,
    amount: str,
    token: str,
    recipient: str,
) -> str:
    """Transfer a specified amount of an asset to a recipient onchain.

    Args:
        provider (BnbChainProvider): The provider to use for the transfer.
        amount (str): The amount of the asset to transfer, e.g. `15`, `0.000001`.
        token (str): The token to transfer, e.g. `BNB` or `0x...`.
        recipient (str): The recipient to transfer the funds (e.g. `0x58dBecc0894Ab4C24F98a0e684c989eD07e4e027`).

    Returns:
        str: A message containing the transfer details.
    """

    client = provider.get_current_client()

    if token == 'BNB':
        tx_hash = client.eth.send_transaction(
            {
                'to': recipient,
                'value': Web3.to_wei(amount, 'ether'),
            }
        )
        token_name = token
    else:
        token_address = Web3.to_checksum_address(token)
        contract = client.eth.contract(token_address, abi=ERC20_ABI)

        token_name = contract.functions.name().call()
        decimals = contract.functions.decimals().call()
        amount_wei = parse_uints(amount, decimals)
        tx_hash = contract.functions.transfer(recipient, amount_wei).transact()

    client.eth.wait_for_transaction_receipt(tx_hash)
    return (
        f'Transferred {amount} {token_name} to {recipient}.\nTransaction hash for the transfer: {tx_hash.to_0x_hex()}'
    )


class TransferAction(BnbChainAction):
    """Transfer action."""

    name: str = 'transfer'
    description: str = TRANSFER_PROMPT
    args_schema: Optional[type[BaseModel]] = TransferInput
    func: Optional[Callable[..., str]] = transfer
