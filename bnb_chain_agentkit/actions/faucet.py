import asyncio
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any, Optional

import websockets
from pydantic import BaseModel, Field
from websockets.exceptions import ConnectionClosed, WebSocketException

from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider

logger = logging.getLogger(__name__)

FAUCET_URL = 'wss://testnet.bnbchain.org/faucet-smart/api'
WEBSOCKET_TIMEOUT = 20  # seconds
MAX_RETRIES = 3

FAUCET_PROMPT = """
This tool will request test tokens from the BNB Chain official faucet.

It takes the token and recipient as inputs.

Important notes:
- The recipient is optional. If not specified, the default account will be used.
- The token is optional. If not specified, BNB will be used.
"""


class FaucetInput(BaseModel):
    """Input argument schema for faucet action."""

    token: str = Field(
        'BNB',
        description='The token to request, e.g. `BNB`, `BTC`, `BUSD`, `DAI`, `ETH`, `USDC`.',
    )
    recipient: Optional[str] = Field(
        None,
        description='The recipient to request the funds. Optional. Could be None or a valid ethereum address starting with "0x".',
    )


async def faucet(
    provider: BnbChainProvider,
    token: str,
    recipient: Optional[str],
) -> str:
    """Request test tokens from the BNB Chain official faucet.

    Args:
        provider (BnbChainProvider): The provider to use for the transfer.
        token (str): The token to request. Could be one of ["BNB", "BTC", "BUSD", "DAI", "ETH", "USDC"].
        recipient (Optional[str]): The recipient to request the funds. Optional. Could be None or a valid ethereum address starting with "0x".

    Returns:
        str: A message containing the transfer details.
    """

    recipient = recipient or provider.get_address()

    headers = {
        'Connection': 'Upgrade',
        'Upgrade': 'websocket',
        'X-Forwarded-For': '127.0.0.1,127.0.0.1',
    }
    message = {
        'tier': 0,
        'url': recipient,
        'symbol': token,
        'captcha': 'noCaptchaToken',
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with websockets.connect(
                FAUCET_URL,
                extra_headers=headers,
                close_timeout=WEBSOCKET_TIMEOUT,
                ping_timeout=WEBSOCKET_TIMEOUT,
            ) as websocket:
                await websocket.send(json.dumps(message))

                try:
                    async with asyncio.timeout(WEBSOCKET_TIMEOUT):
                        while True:
                            response = await websocket.recv()
                            response_data = json.loads(response)

                            if 'error' in response_data:
                                return f'Error from faucet: {response_data["error"]}'

                            requests = response_data.get('requests', [])
                            if len(requests) > 0:
                                tx_hash = requests[0]['tx']['hash']
                                return f'Successfully requested {token} for {recipient}. Transaction hash: {tx_hash}'

                except asyncio.TimeoutError:
                    if attempt < MAX_RETRIES - 1:
                        continue
                    return 'Request timed out while waiting for faucet response'

        except ConnectionClosed:
            if attempt < MAX_RETRIES - 1:
                continue
            return 'Connection closed by faucet server'
        except WebSocketException as e:
            return f'WebSocket error: {str(e)}'
        except Exception as e:
            return f'Unexpected error: {str(e)}'

    return 'Failed to get response from faucet after maximum retries'


class FaucetAction(BnbChainAction):
    """Faucet action."""

    name: str = 'faucet'
    description: str = FAUCET_PROMPT
    args_schema: Optional[type[BaseModel]] = FaucetInput
    async_func: Optional[Callable[..., Coroutine[Any, Any, str]]] = faucet
