# bnb_chain_agentkit/actions/transaction_analytics.py
from pydantic import BaseModel, Field
from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider
from web3 import Web3

# --- Gas Fee Estimation Tool ---

class GasFeeEstimationInput(BaseModel):
    # No input parameters needed.
    pass

def get_gas_fee(provider: BnbChainProvider) -> str:
    client = provider.get_current_client()
    gas_price = client.eth.gas_price  # in wei
    gas_price_gwei = Web3.from_wei(gas_price, 'gwei')
    return f"Current gas price is {gas_price_gwei} Gwei."

class GasFeeEstimationAction(BnbChainAction):
    name: str = "get_gas_fee"
    description: str = "Estimate current gas fee (in Gwei)."
    args_schema: type[BaseModel] = GasFeeEstimationInput
    func = get_gas_fee

# --- Transaction Receipt / Analytics Tool ---

class TransactionReceiptInput(BaseModel):
    tx_hash: str = Field(..., description="Transaction hash to retrieve details for.")

def get_transaction_receipt(provider: BnbChainProvider, tx_hash: str) -> str:
    client = provider.get_current_client()
    try:
        receipt = client.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        return f"Error retrieving transaction receipt: {str(e)}"
    # Optionally, also fetch the original transaction details.
    try:
        tx = client.eth.get_transaction(tx_hash)
    except Exception:
        tx = None
    details = f"Transaction Receipt for {tx_hash}:\n"
    details += f"  Status: {'Success' if receipt.status == 1 else 'Failure'}\n"
    details += f"  Block Number: {receipt.blockNumber}\n"
    details += f"  Gas Used: {receipt.gasUsed}\n"
    if tx is not None:
        details += f"  Gas Price: {Web3.from_wei(tx.gasPrice, 'gwei')} Gwei\n"
        tx_fee = tx.gasPrice * receipt.gasUsed
        details += f"  Transaction Fee: {Web3.from_wei(tx_fee, 'ether')} BNB\n"
    details += f"  Contract Address: {receipt.contractAddress}\n"
    details += f"  Logs Count: {len(receipt.logs)}\n"
    return details

class TransactionReceiptAction(BnbChainAction):
    name: str = "get_transaction_receipt"
    description: str = "Retrieve and display transaction details given a transaction hash."
    args_schema: type[BaseModel] = TransactionReceiptInput
    func = get_transaction_receipt
