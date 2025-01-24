import logging
from collections.abc import Callable
from typing import Optional

from pydantic import BaseModel, Field
from web3 import Web3

from langchain_bnb_chain.actions.abi import ERC20_ABI, L1_STANDARD_BRIDGE_ABI, L2_STANDARD_BRIDGE_ABI
from langchain_bnb_chain.actions.bnb_chain_action import BnbChainAction
from langchain_bnb_chain.actions.utils.uints import parse_uints
from langchain_bnb_chain.provider.bnb_chain_provider import BnbChainProvider, SupportedChain

logger = logging.getLogger(__name__)

L1_BRIDGE_ADDRESS = Web3.to_checksum_address('0xF05F0e4362859c3331Cb9395CBC201E3Fa6757Ea')
L2_BRIDGE_ADDRESS = Web3.to_checksum_address('0x4000698e3De52120DE28181BaACda82B21568416')
LEGACY_ERC20_ETH_ADDRESS = Web3.to_checksum_address('0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000')

BRIDGE_PROMPT = """
This tool helps bridge tokens between BSC and opBNB.

It takes from_chain, to_chain, from_token, to_token, amount, and recipient as inputs.

Important notes:
- There are some similar expressions for the bridge action. For example:
    - "Bridge 1 BNB from BSC to opBNB"
    - "Deposit 1 BNB from BSC to opBNB"
    - "Withdraw 1 BNB from opBNB to BSC"
- from_chain and to_chain must be different.
- If from_token is not provided, the native asset (BNB) will be bridged. In this case, to_token must be None.
- When bridging from opBNB to BSC, the to_token should always be None.
- When bridging from opBNB to BSC, there is a delegation fee for the claim bot. Make sure to have enough funds to cover this fee.
"""


class BridgeInput(BaseModel):
    """Input argument schema for bridge action."""

    from_chain: SupportedChain = Field(description='The chain to bridge from.')
    to_chain: SupportedChain = Field(description='The chain to bridge to.')
    from_token: Optional[str] = Field(
        None,
        description='The token to bridge from. Optional. Could be None or a valid ethereum address starting with "0x".',
    )
    to_token: Optional[str] = Field(
        None,
        description='The token to bridge to. Optional. Could be None or a valid ethereum address starting with "0x".',
    )
    amount: str = Field(description='The amount to perform the action on, e.g. `15`, `0.000001`.')
    recipient: Optional[str] = Field(
        None,
        description='The recipient to bridge the funds to. Must be a valid Ethereum address starting with "0x". Optional. Could be None or a valid ethereum address starting with "0x".',
    )


def bridge(
    provider: BnbChainProvider,
    from_chain: SupportedChain,
    to_chain: SupportedChain,
    from_token: Optional[str],
    to_token: Optional[str],
    amount: str,
    recipient: Optional[str],
) -> str:
    """Bridge tokens between BSC and opBNB.

    Args:
        provider (BnbChainProvider): The provider to use for the bridge.
        from_chain (SupportedChain): The chain to bridge from.
        to_chain (SupportedChain): The chain to bridge to.
        from_token (Optional[str]): The token contract address to bridge from. Optional. Could be None or a valid ethereum address starting with "0x".
        to_token (Optional[str]): The token contract address to bridge to. Optional. Could be None or a valid ethereum address starting with "0x".
        amount (str): The amount to perform the action on, e.g. `15`, `0.000001`.
        recipient (Optional[str]): The recipient to bridge the funds to. Optional. Could be None or a valid ethereum address starting with "0x".

    Returns:
        str: A message containing the action details.
    """

    address = provider.get_address()

    from_token = from_token or 'BNB'
    self_bridge = recipient is None or recipient == address
    native_token_bridge = from_token == 'BNB'

    client = provider.get_client(from_chain)
    if from_chain == SupportedChain.BSC and to_chain == SupportedChain.OPBNB:
        l1_bridge = client.eth.contract(L1_BRIDGE_ADDRESS, abi=L1_STANDARD_BRIDGE_ABI)

        if native_token_bridge:
            amount_wei = Web3.to_wei(amount, 'ether')

            if self_bridge:
                tx_hash = l1_bridge.functions.depositETH(1, '0x').transact({'value': amount_wei})
            else:
                tx_hash = l1_bridge.functions.depositETHTo(recipient, 1, '0x').transact({'value': amount_wei})
        else:
            if to_token is None:
                raise ValueError('to_token must be provided when bridging ERC20 from BSC to opBNB')

            token_address = Web3.to_checksum_address(from_token)  # type: ignore
            contract = client.eth.contract(token_address, abi=ERC20_ABI)
            decimals = contract.functions.decimals().call()
            amount_wei = parse_uints(amount, decimals)

            # check ERC20 allowance
            allowance = contract.functions.allowance(address, L1_BRIDGE_ADDRESS).call()
            if allowance < amount_wei:
                logger.info(f'Increasing allowance for L1 bridge. {amount_wei - allowance} more needed.')
                tx_hash = contract.functions.approve(L1_BRIDGE_ADDRESS, amount_wei).transact()
                client.eth.wait_for_transaction_receipt(tx_hash)

            if self_bridge:
                tx_hash = l1_bridge.functions.depositERC20(from_token, to_token, amount_wei, 1, '0x').transact()
            else:
                tx_hash = l1_bridge.functions.depositERC20To(
                    from_token, to_token, recipient, amount_wei, 1, '0x'
                ).transact()

    elif from_chain == SupportedChain.OPBNB and to_chain == SupportedChain.BSC:
        l2_bridge = client.eth.contract(L2_BRIDGE_ADDRESS, abi=L2_STANDARD_BRIDGE_ABI)
        delegation_fee = l2_bridge.functions.delegationFee().call()

        if native_token_bridge:
            amount_wei = Web3.to_wei(amount, 'ether')
            value = amount_wei + delegation_fee

            if self_bridge:
                tx_hash = l2_bridge.functions.withdraw(LEGACY_ERC20_ETH_ADDRESS, amount_wei, 1, '0x').transact(
                    {'value': value}
                )
            else:
                tx_hash = l2_bridge.functions.withdrawTo(
                    LEGACY_ERC20_ETH_ADDRESS, recipient, amount_wei, 1, '0x'
                ).transact({'value': value})
        else:
            token_address = Web3.to_checksum_address(from_token)  # type: ignore
            contract = client.eth.contract(token_address, abi=ERC20_ABI)
            decimals = contract.functions.decimals().call()
            amount_wei = parse_uints(amount, decimals)

            # check ERC20 allowance
            allowance = contract.functions.allowance(address, L2_BRIDGE_ADDRESS).call()
            if allowance < amount_wei:
                logger.info(f'Increasing allowance for L2 bridge. {amount_wei - allowance} more needed.')
                tx_hash = contract.functions.approve(L2_BRIDGE_ADDRESS, amount_wei).transact()
                client.eth.wait_for_transaction_receipt(tx_hash)

            if self_bridge:
                tx_hash = l2_bridge.functions.withdraw(from_token, amount_wei, 1, '0x').transact(
                    {'value': delegation_fee}
                )
            else:
                tx_hash = l2_bridge.functions.withdrawTo(from_token, recipient, amount_wei, 1, '0x').transact(
                    {'value': delegation_fee}
                )

    else:
        raise ValueError(f'Invalid bridge direction: {from_chain} to {to_chain}')

    return f'Bridge {amount} {from_token} from {from_chain.value} to {to_chain.value}. Transaction hash: {tx_hash.to_0x_hex()}'


class BridgeAction(BnbChainAction):
    """Bridge action."""

    name: str = 'bridge'
    description: str = BRIDGE_PROMPT
    args_schema: Optional[type[BaseModel]] = BridgeInput
    func: Optional[Callable[..., str]] = bridge
