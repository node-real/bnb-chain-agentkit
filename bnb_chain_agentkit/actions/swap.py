import logging
from collections.abc import Callable
from typing import Optional

from pydantic import BaseModel, Field
from web3 import Web3

from bnb_chain_agentkit.actions.abi import (
    ERC20_ABI,
    IPANCAKE_QUOTER_V2_ABI,
    IPANCAKE_V3_FACTORY_ABI,
    IPANCAKE_V3_POOL_ABI,
    IPANCAKE_V3_ROUTER_ABI,
    WBNB_ABI,
)
from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.actions.utils.uints import parse_uints
from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider, SupportedChain

logger = logging.getLogger(__name__)

DEPLOYMENTS = {
    SupportedChain.BSC: {
        'factory': '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
        'router': '0x1b81D678ffb9C0263b24A97847620C99d213eB14',
        'wbnb': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
        'quoter': '0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997',
    },
    SupportedChain.OPBNB: {
        'factory': '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
        'router': '0x1b81D678ffb9C0263b24A97847620C99d213eB14',
        'wbnb': '0x4200000000000000000000000000000000000006',
    },
}

POOL_FEES_BPS = [100, 500, 2500, 10000]

SWAP_PROMPT = """
This tool helps swap tokens on Pancake V3.

It takes chain, input token, output token, amount and slippage as inputs.

Important notes:
- Only support exact input swap.
- Input token and output token could be valid token addresses or "BNB".
- Slippage is a percentage, e.g. `100` means 1%.
"""


class SwapInput(BaseModel):
    """Input argument schema for swap action."""

    chain: SupportedChain = Field(SupportedChain.BSC, description='The chain to perform the swap on.')
    input_token: str = Field(description='The input token to swap, e.g. `BNB` or `0x...`.')
    output_token: str = Field(description='The output token to swap to, e.g. `BNB` or `0x...`.')
    amount: str = Field(description='The amount to perform the action on, e.g. `15`, `0.000001`.')
    slippage: int = Field(50, description='The slippage to use for the swap, e.g. `100` means 1%.')


def swap(
    provider: BnbChainProvider,
    chain: SupportedChain,
    input_token: str,
    output_token: str,
    amount: str,
    slippage: int,
) -> str:
    """Swap tokens on Pancake V3.

    Args:
        provider (BnbChainProvider): The provider to use for the swap.
        chain: The chain to perform the swap on.
        input_token (str): The input token to swap, e.g. `BNB` or `0x...`.
        output_token (str): The output token to swap to, e.g. `BNB` or `0x...`.
        amount (str): The amount to perform the swap on, e.g. `15`, `0.000001`.
        slippage (Optional[int]): The slippage to use for the swap, e.g. `100` means 1%.

    Returns:
        str: A message containing the action details.
    """

    client = provider.get_client(chain)
    address = provider.get_address()

    # convert to WBNB if needed
    if input_token == 'BNB':
        input_token = DEPLOYMENTS[chain]['wbnb']
        wbnb = client.eth.contract(address=Web3.to_checksum_address(input_token), abi=WBNB_ABI)
        balance = wbnb.functions.balanceOf(address).call()
        amount_wei = Web3.to_wei(amount, 'ether')
        if balance < amount_wei:
            logger.info('Deposit BNB to WBNB contract to perform the swap.')
            tx_hash = wbnb.functions.deposit().transact({'value': amount_wei - balance})
            client.eth.wait_for_transaction_receipt(tx_hash)

    withdraw_wbnb = False
    if output_token == 'BNB':
        output_token = DEPLOYMENTS[chain]['wbnb']
        wbnb = client.eth.contract(address=Web3.to_checksum_address(output_token), abi=WBNB_ABI)
        before_balance = wbnb.functions.balanceOf(address).call()
        withdraw_wbnb = True

    input_token = Web3.to_checksum_address(input_token)
    output_token = Web3.to_checksum_address(output_token)

    # check allowance
    token = client.eth.contract(address=input_token, abi=ERC20_ABI)
    decimals = token.functions.decimals().call()
    amount_wei = parse_uints(amount, decimals)
    allowance = token.functions.allowance(address, DEPLOYMENTS[chain]['router']).call()
    if allowance < amount_wei:
        logger.info('Approve the router to spend the input token.')
        tx_hash = token.functions.approve(DEPLOYMENTS[chain]['router'], amount_wei).transact()
        client.eth.wait_for_transaction_receipt(tx_hash)

    factory = client.eth.contract(
        address=Web3.to_checksum_address(DEPLOYMENTS[chain]['factory']), abi=IPANCAKE_V3_FACTORY_ABI
    )

    # check pool liquidity
    best_fee = 0
    best_liquidity = 0
    for fee in POOL_FEES_BPS:
        pool = factory.functions.getPool(
            input_token,
            output_token,
            fee,
        ).call()
        if pool == '0x0000000000000000000000000000000000000000':
            continue
        pool = client.eth.contract(address=Web3.to_checksum_address(pool), abi=IPANCAKE_V3_POOL_ABI)
        liquidity = pool.functions.liquidity().call()
        if liquidity > best_liquidity:
            best_liquidity = liquidity
            best_fee = fee

    if best_liquidity == 0:
        return 'No liquidity found for the given input and output token.'

    logger.info(f'Using fee {best_fee / 10000}% for the swap.')

    # calculate min amount out
    if slippage > 0:
        min_amount_out = calc_min_amount_out(
            client, DEPLOYMENTS[chain]['quoter'], input_token, output_token, amount_wei, best_fee, slippage
        )
    else:
        min_amount_out = 0

    router = client.eth.contract(
        address=Web3.to_checksum_address(DEPLOYMENTS[chain]['router']), abi=IPANCAKE_V3_ROUTER_ABI
    )
    deadline = client.eth.get_block('latest').timestamp + 300
    params = {
        'tokenIn': input_token,
        'tokenOut': output_token,
        'fee': best_fee,
        'recipient': address,
        'deadline': deadline,
        'amountIn': amount_wei,
        'amountOutMinimum': min_amount_out,
        'sqrtPriceLimitX96': 0,  # No price limit
    }

    tx_hash = router.functions.exactInputSingle(params).transact()
    client.eth.wait_for_transaction_receipt(tx_hash)

    if withdraw_wbnb:
        logger.info('Withdrawing WBNB to BNB.')
        after_balance = wbnb.functions.balanceOf(address).call()
        if after_balance > before_balance:
            tx_hash = wbnb.functions.withdraw(after_balance - before_balance).transact()
            client.eth.wait_for_transaction_receipt(tx_hash)

    return f'Swap action completed. Transaction hash: {tx_hash.to_0x_hex()}'


def calc_min_amount_out(
    client: Web3, quoter_address: str, input_token: str, output_token: str, amount_in: int, fee: int, slippage: int
) -> int:
    quoter = client.eth.contract(address=Web3.to_checksum_address(quoter_address), abi=IPANCAKE_QUOTER_V2_ABI)

    params = {
        'tokenIn': input_token,
        'tokenOut': output_token,
        'fee': fee,
        'amountIn': amount_in,
        'sqrtPriceLimitX96': 0,  # No price limit
    }
    results = quoter.functions.quoteExactInputSingle(params).call()
    return int(results[0] * 10_000 // (10_000 + slippage))


class SwapAction(BnbChainAction):
    """Swap action."""

    name: str = 'swap'
    description: str = SWAP_PROMPT
    args_schema: Optional[type[BaseModel]] = SwapInput
    func: Optional[Callable[..., str]] = swap
