from enum import Enum
from typing import Optional

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware, SignAndSendRawMiddlewareBuilder


class SupportedChain(Enum):
    BSC = 'BSC'
    OPBNB = 'opBNB'


CHAIN_ID_BSC = 56
CHAIN_ID_OPBNB = 204


class BnbChainProvider:
    """
    BnbChainProvider is a provider for the BNB Chain API.
    """

    address: ChecksumAddress
    current_client: Web3
    clients: dict[SupportedChain, Web3]

    def __init__(self, private_key: str, bsc_provider_url: str, opbnb_provider_url: Optional[str] = None):
        w3 = Web3(Web3.HTTPProvider(bsc_provider_url))
        if not w3.is_connected():
            raise ValueError('Failed to connect to BSC provider')

        if w3.eth.chain_id != CHAIN_ID_BSC:
            raise ValueError('BSC provider is not connected to BSC')

        account = w3.eth.account.from_key(private_key)
        self.address = account.address

        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        w3.middleware_onion.add(SignAndSendRawMiddlewareBuilder.build(account))  # type: ignore
        w3.eth.default_account = self.address

        self.current_client = w3
        self.clients = {
            SupportedChain.BSC: w3,
        }

        if opbnb_provider_url:
            w3 = Web3(Web3.HTTPProvider(opbnb_provider_url))
            if not w3.is_connected():
                raise ValueError('Failed to connect to OPBNB provider')

            if w3.eth.chain_id != CHAIN_ID_OPBNB:
                raise ValueError('opBNB provider is not connected to opBNB')

            w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(account), layer=0)  # type: ignore
            w3.eth.default_account = account.address

            self.clients[SupportedChain.OPBNB] = w3

    def get_address(self) -> ChecksumAddress:
        return self.address

    def get_client(self, chain: SupportedChain) -> Web3:
        client = self.clients.get(chain)
        if client is None:
            raise ValueError(f'Client for chain {chain} not found')
        return client

    def get_current_client(self) -> Web3:
        return self.current_client

    def switch_client(self, chain: SupportedChain):
        if chain not in self.clients:
            raise ValueError(f'Client for chain {chain} not found')

        self.current_client = self.clients[chain]
