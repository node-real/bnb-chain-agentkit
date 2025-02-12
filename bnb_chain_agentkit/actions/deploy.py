import logging
import os
from collections.abc import Callable
from enum import Enum
from typing import Optional

from eth_typing import ChecksumAddress
from pydantic import BaseModel, Field
from solcx import compile_source, install_solc_pragma, set_solc_version_pragma
from solcx.exceptions import SolcNotInstalled
from web3 import Web3

from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider, SupportedChain

logger = logging.getLogger(__name__)

_solc_pragma = 'pragma solidity ^0.8.22;'

DEPLOY_PROMPT = """
This tool helps deploy an ERC contract on BSC or opBNB.

It takes contract type, token name, token symbol, initial supply, base uri and chain as inputs.

Important notes:
- For ERC20, token name and token symbol are required.
- For ERC721, token name, token symbol and base uri are required.
- For ERC1155, uri is required.
- The initial supply is in ether. If not specified, it is set to default value of 1000000000000000000.
"""


class ContractType(Enum):
    ERC20 = 'ERC20'
    ERC721 = 'ERC721'
    ERC1155 = 'ERC1155'


class DeployInput(BaseModel):
    """Input argument schema for deploy action."""

    contract_type: ContractType = Field(description='The contract type to deploy.')
    token_name: Optional[str] = Field(None, description='The token name. Must be provided for ERC20 and ERC721.')
    token_symbol: Optional[str] = Field(None, description='The token symbol. Must be provided for ERC20 and ERC721.')
    initial_supply: Optional[str] = Field('1000000000000000000', description='The initial supply.')
    base_uri: Optional[str] = Field(None, description='The base uri. Must be provided for ERC721 and ERC1155.')
    chain: SupportedChain = Field(SupportedChain.BSC, description='The chain to perform the deploy on.')


def deploy(
    provider: BnbChainProvider,
    contract_type: ContractType,
    token_name: Optional[str],
    token_symbol: Optional[str],
    initial_supply: Optional[str],
    base_uri: Optional[str],
    chain: SupportedChain,

) -> str:
    """Deploy an ERC contract on BSC or opBNB.

    Args:
        provider (BnbChainProvider): The provider to use for the deploy.
        contract_type (ContractType): The contract type to deploy.
        token_name (str): The token name.
        token_symbol (Optional[str]): The token symbol.
        initial_supply (Optional[str]): The initial supply.
        base_uri (Optional[str]): The base uri.
        chain (Optional[str]): The chain to perform the swap on.

    Returns:
        str: A message containing the action details.
    """

    client = provider.get_client(chain)
    account = provider.get_address()

    prepare_solc()
    if contract_type == ContractType.ERC20:
        if token_name is None:
            return 'Token name is required for ERC20.'
        if token_symbol is None:
            return 'Token symbol is required for ERC20.'

        initial_supply_wei = Web3.to_wei(initial_supply, 'wei') if initial_supply else 0
        print("initial_supply is " + str(initial_supply) , "initial_supply_wei is " +str(initial_supply_wei))
        contract_address = deploy_contract(client, 'ERC20', token_name, token_symbol, initial_supply_wei, account)
    elif contract_type == ContractType.ERC721:
        if token_name is None:
            return 'Token name is required for ERC721.'
        if token_symbol is None:
            return 'Token symbol is required for ERC721.'
        if base_uri is None:
            return 'Base uri is required for ERC721.'

        contract_address = deploy_contract(client, 'ERC721', token_name, token_symbol, base_uri, account)
    elif contract_type == ContractType.ERC1155:
        if base_uri is None:
            return 'Base uri is required for ERC1155.'

        contract_address = deploy_contract(client, 'ERC1155', base_uri, account)

    return f'{contract_type.value} deployed successfully. Contract address: {contract_address}'


def deploy_contract(client: Web3, contract_name: str, *args) -> ChecksumAddress:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    contract_path = os.path.join(current_dir, 'contracts', f'{contract_name}.sol')
    with open(contract_path, 'r') as c:
        compiled_sol = compile_source(
            c.read(),
            output_values=['abi', 'bin'],
            optimize=True,
            optimize_runs=200,
        )

    contract_interface = compiled_sol[f'<stdin>:{contract_name}Contract']
    bytecode = contract_interface['bin']
    abi = contract_interface['abi']

    if len(bytecode) == 0:
        raise ValueError('Bytecode is empty')

    contract = client.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract.constructor(*args).transact()
    receipt = client.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.contractAddress  # type: ignore


def prepare_solc():
    try:
        set_solc_version_pragma(_solc_pragma)
    except SolcNotInstalled:
        logger.info('No compatible solc version installed. Installing...')
        install_solc_pragma(_solc_pragma, show_progress=True)


class DeployAction(BnbChainAction):
    """Deploy action."""

    name: str = 'deploy'
    description: str = DEPLOY_PROMPT
    args_schema: Optional[type[BaseModel]] = DeployInput
    func: Optional[Callable[..., str]] = deploy
