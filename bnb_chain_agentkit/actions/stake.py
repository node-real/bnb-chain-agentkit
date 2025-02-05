import logging
from collections.abc import Callable
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from web3 import Web3

from bnb_chain_agentkit.actions.abi import ERC20_ABI, LISTA_DAO_ABI
from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider

logger = logging.getLogger(__name__)

LISTA_DAO_ADDRESS = Web3.to_checksum_address('0x1adB950d8bB3dA4bE104211D5AB038628e477fE6')
SLIS_BNB_ADDRESS = Web3.to_checksum_address('0xB0b84D294e0C75A6abe60171b70edEb2EFd14A1B')

STAKE_PROMPT = """
This tool helps stake BNB to Lista DAO on BSC.

It takes the action type and the amount as inputs.

Important notes:
- The DEPOSIT action could have several similar expressions, e.g. "delegate" or "stake".
- Amount is required for the DEPOSIT action.
- The WITHDRAW action could have several similar expressions, e.g. "undelegate" or "unstake".
- Amount is optional for the WITHDRAW action. If not provided, the entire balance will be withdrawn.
- Staking can only be done on the BSC mainnet.
- Ensure there is sufficient balance for the DEPOSIT action itself AND the gas cost of this action.
"""


class Action(Enum):
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'
    CLAIM = 'claim'


class StakeInput(BaseModel):
    """Input argument schema for stake action."""

    action: Action = Field(description='The action to perform.')
    amount: str = Field('0', description='The amount to perform the action on, e.g. `15`, `0.000001`.')


def stake(
    provider: BnbChainProvider,
    action: Action,
    amount: str,
) -> str:
    """Stake related actions on Lista DAO on BSC.

    Args:
        provider (BnbChainProvider): The provider to use for the transfer.
        action (Action): The action to perform.
        amount (str): The amount to perform the action on, e.g. `15`, `0.000001`.

    Returns:
        str: A message containing the action details.
    """

    client = provider.get_current_client()
    address = provider.get_address()

    if client.eth.chain_id != 56:
        return 'This tool can only be used on the BSC mainnet.'

    if action == Action.DEPOSIT:
        if amount == '0':
            return 'Amount is required for the "deposit" action.'
        return do_deposit(client, address, amount)
    elif action == Action.WITHDRAW:
        return do_withdraw(client, address, amount)
    elif action == Action.CLAIM:
        return do_claim(client, address)


def do_deposit(client: Web3, address: str, amount: str) -> str:
    amount_wei = Web3.to_wei(amount, 'ether')
    lista_dao = client.eth.contract(LISTA_DAO_ADDRESS, abi=LISTA_DAO_ABI)
    tx_hash = lista_dao.functions.deposit(amount_wei).transact({'value': amount_wei})
    client.eth.wait_for_transaction_receipt(tx_hash)

    slis_bnb = client.eth.contract(SLIS_BNB_ADDRESS, abi=ERC20_ABI)
    balance = slis_bnb.functions.balanceOf(address).call()
    balance_formatted = Web3.from_wei(balance, 'ether')

    return f'Deposited {amount} BNB to Lista DAO. Transaction hash: {tx_hash.to_0x_hex()}\nBalance of slisBNB: {balance_formatted}'


def do_withdraw(client: Web3, address: str, amount: str) -> str:
    slis_bnb = client.eth.contract(SLIS_BNB_ADDRESS, abi=ERC20_ABI)

    # If amount is None, withdraw the entire balance
    if amount == '0':
        amount_wei = slis_bnb.functions.balanceOf(address).call()
        amount = Web3.from_wei(amount_wei, 'ether')  # type: ignore
    else:
        amount_wei = Web3.to_wei(amount, 'ether')

    # check allowance
    allowance = slis_bnb.functions.allowance(address, LISTA_DAO_ADDRESS).call()
    if allowance < amount_wei:
        logger.info(f'Increasing allowance for Lista DAO. {amount_wei - allowance} more needed.')
        tx_hash = slis_bnb.functions.approve(LISTA_DAO_ADDRESS, amount_wei).transact()
        client.eth.wait_for_transaction_receipt(tx_hash)

    lista_dao = client.eth.contract(LISTA_DAO_ADDRESS, abi=LISTA_DAO_ABI)
    tx_hash = lista_dao.functions.requestWithdraw(amount_wei).transact()
    client.eth.wait_for_transaction_receipt(tx_hash)

    balance = slis_bnb.functions.balanceOf(address).call()
    balance_formatted = Web3.from_wei(balance, 'ether')

    return f'Requested to withdraw {amount} slisBNB from Lista DAO (Need 7 days to be claimed). Transaction hash: {tx_hash.to_0x_hex()}\nBalance of slisBNB: {balance_formatted}'


def do_claim(client: Web3, address: str) -> str:
    lista_dao = client.eth.contract(LISTA_DAO_ADDRESS, abi=LISTA_DAO_ABI)
    requests = lista_dao.functions.getUserWithdrawalRequests(address).call()

    total_claimed = 0
    for i in range(len(requests)):
        is_claimable, amount = lista_dao.functions.getUserRequestStatus(address, i).call()
        if is_claimable:
            tx_hash = lista_dao.functions.claimWithdraw(i).transact()
            client.eth.wait_for_transaction_receipt(tx_hash)
            total_claimed += amount
        else:
            break

    total_claimed_formatted = Web3.from_wei(total_claimed, 'ether')

    return f'Claimed {total_claimed_formatted} slisBNB from Lista DAO. Transaction hash: {tx_hash.to_0x_hex()}'


class StakeAction(BnbChainAction):
    """Stake action."""

    name: str = 'stake'
    description: str = STAKE_PROMPT
    args_schema: Optional[type[BaseModel]] = StakeInput
    func: Optional[Callable[..., str]] = stake
