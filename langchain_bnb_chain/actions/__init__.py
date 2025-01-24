from langchain_bnb_chain.actions.bnb_chain_action import BnbChainAction
from langchain_bnb_chain.actions.bridge import BridgeAction
from langchain_bnb_chain.actions.deploy import DeployAction
from langchain_bnb_chain.actions.faucet import FaucetAction
from langchain_bnb_chain.actions.get_balance import GetBalanceAction
from langchain_bnb_chain.actions.stake import StakeAction
from langchain_bnb_chain.actions.swap import SwapAction
from langchain_bnb_chain.actions.transfer import TransferAction


def get_all_bnb_chain_actions() -> list[type[BnbChainAction]]:
    """Retrieve all subclasses of BnbChainAction defined in the package."""
    actions = []
    for action in BnbChainAction.__subclasses__():
        actions.append(action())  # type: ignore
    return actions


BNB_CHAIN_ACTIONS = get_all_bnb_chain_actions()

__all__ = [
    'BNB_CHAIN_ACTIONS',
    'BnbChainAction',
    'GetBalanceAction',
    'TransferAction',
    'StakeAction',
    'FaucetAction',
    'BridgeAction',
    'DeployAction',
    'SwapAction',
]
