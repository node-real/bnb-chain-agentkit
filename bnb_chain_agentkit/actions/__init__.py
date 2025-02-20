from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.actions.bridge import BridgeAction
from bnb_chain_agentkit.actions.deploy import DeployAction
from bnb_chain_agentkit.actions.faucet import FaucetAction
from bnb_chain_agentkit.actions.get_balance import GetBalanceAction
from bnb_chain_agentkit.actions.stake import StakeAction
from bnb_chain_agentkit.actions.swap import SwapAction
from bnb_chain_agentkit.actions.transfer import TransferAction

from bnb_chain_agentkit.actions.transaction_analytics import (
    GasFeeEstimationAction,
    TransactionReceiptAction,
    GasFeeEstimationAction,
    RecentTransactionsAction,
    PendingTransactionTrackerAction,
    GasPriceTrendAnalyzerAction,
    TransactionFeeEstimatorAction,
    TransactionVolumeAnalyzerAction,
    TokenTransferHistoryAction,
)
from bnb_chain_agentkit.actions.token_price import TokenPriceQueryAction


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
    'GasFeeEstimationAction',
    'TransactionReceiptAction',
    'TokenPriceQueryAction',
    'RecentTransactionsAction',
    'PendingTransactionTrackerAction',
    'GasPriceTrendAnalyzerAction',
    'TransactionFeeEstimatorAction',
    'TransactionVolumeAnalyzerAction',
    'TokenTransferHistoryAction'
]
