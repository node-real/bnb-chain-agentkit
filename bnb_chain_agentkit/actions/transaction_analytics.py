import os
import time
import requests
from pydantic import BaseModel, Field
from bnb_chain_agentkit.actions.bnb_chain_action import BnbChainAction
from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider
from web3 import Web3

# A mapping for token symbols to contract addresses:
TOKEN_CONTRACT_ADDRESSES = {
    "BUSD": "0xe9e7cea3dedca5984780bafc599bd69add087d56",
    "BSC-USD":"0x55d398326f99059fF775485246999027B3197955", 
    "BUSD-T":"0x55d398326f99059ff775485246999027b3197955",
    "BEP20Ethereum":"0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
    "ETH":"0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
    "WBNB":"0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    "Wrapped BNB":"0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    "BTCB":"0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
    "BTCB Token":"0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
}

# --------------------------------------------------------------------
# 1. Gas Fee Estimation Tool
# --------------------------------------------------------------------

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

# --------------------------------------------------------------------
# 2. Transaction Receipt / Analytics Tool
# --------------------------------------------------------------------

class TransactionReceiptInput(BaseModel):
    tx_hash: str = Field(..., description="Transaction hash to retrieve details for.")

def get_transaction_receipt(provider: BnbChainProvider, tx_hash: str) -> str:
    client = provider.get_current_client()
    try:
        receipt = client.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        return f"Error retrieving transaction receipt: {str(e)}"
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

# --------------------------------------------------------------------
# 3. Recent Transactions Fetcher
# --------------------------------------------------------------------

class RecentTransactionsInput(BaseModel):
    address: str = Field(..., description="Address to fetch recent transactions for.")
    limit: int = Field(5, description="Number of transactions to retrieve.")

def get_recent_transactions(provider: BnbChainProvider, address: str, limit: int = 5) -> str:
    api_key = os.environ.get("BSCSCAN_API_KEY")
    if not api_key:
        return "BSCSCAN_API_KEY not set in environment."
    url = (
        f"https://api.bscscan.com/api?module=account&action=txlist&address={address}"
        f"&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={api_key}"
    )
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") != "1":
            return f"Error fetching transactions: {data.get('message', 'Unknown error')}"
        txs = data.get("result", [])
        result = f"Recent transactions for address {address}:\n"
        for i, tx in enumerate(txs, 1):
            value_bnb = Web3.from_wei(int(tx['value']), 'ether')
            status = "Success" if tx.get("isError") == "0" else "Failure"
            result += f"{i}. TxHash: {tx['hash']} – Block: {tx['blockNumber']} – Value: {value_bnb} BNB – Status: {status}\n"
        return result
    except Exception as e:
        return f"Error fetching transactions: {str(e)}"

class RecentTransactionsAction(BnbChainAction):
    name: str = "recent_transactions"
    description: str = "Retrieve the recent transactions for a given address."
    args_schema: type[BaseModel] = RecentTransactionsInput
    func = get_recent_transactions

# --------------------------------------------------------------------
# 4. Pending Transaction Tracker
# --------------------------------------------------------------------

class PendingTransactionsInput(BaseModel):
    address: str = Field(..., description="Address to track pending transactions for.")
    limit: int = Field(5, description="Maximum number of pending transactions to return.")

def get_pending_transactions(provider: BnbChainProvider, address: str, limit: int = 5) -> str:
    client = provider.get_current_client()
    try:
        pending_filter = client.eth.filter("pending")
        pending_tx_hashes = pending_filter.get_new_entries()
    except Exception as e:
        return f"Error creating pending filter: {str(e)}"
    
    matching_txs = []
    for tx_hash in pending_tx_hashes:
        try:
            tx = client.eth.get_transaction(tx_hash)
            if tx is None:
                continue
            if tx['from'].lower() == address.lower() or (tx.get('to') and tx['to'].lower() == address.lower()):
                matching_txs.append(tx)
                if len(matching_txs) >= limit:
                    break
        except Exception:
            continue
    if not matching_txs:
        return f"No pending transactions found for address {address}."
    result = f"Pending transactions for address {address}:\n"
    for i, tx in enumerate(matching_txs, 1):
        gas_price_gwei = Web3.from_wei(tx.gasPrice, 'gwei')
        result += f"{i}. TxHash: {tx.hash.hex()} – Gas Price: {gas_price_gwei} Gwei\n"
    return result

class PendingTransactionTrackerAction(BnbChainAction):
    name: str = "pending_transactions"
    description: str = "Track and list pending transactions for a given address."
    args_schema: type[BaseModel] = PendingTransactionsInput
    func = get_pending_transactions

# --------------------------------------------------------------------
# 5. Gas Price Trend Analyzer
# --------------------------------------------------------------------

class GasPriceTrendInput(BaseModel):
    num_blocks: int = Field(10, description="Number of recent blocks to analyze for gas price trend.")

def get_gas_price_trend(provider: BnbChainProvider, num_blocks: int = 10) -> str:
    client = provider.get_current_client()
    latest_block = client.eth.get_block('latest', full_transactions=True)
    latest_block_number = latest_block.number
    total_gas_price = 0
    tx_count = 0
    for i in range(latest_block_number, latest_block_number - num_blocks, -1):
        try:
            block = client.eth.get_block(i, full_transactions=True)
            for tx in block.transactions:
                total_gas_price += tx.gasPrice
                tx_count += 1
        except Exception:
            continue
    if tx_count == 0:
        return "No transactions found in recent blocks."
    avg_gas_price = total_gas_price // tx_count
    avg_gas_price_gwei = Web3.from_wei(avg_gas_price, 'gwei')
    return f"Average gas price over the last {num_blocks} blocks is approximately {avg_gas_price_gwei} Gwei."

class GasPriceTrendAnalyzerAction(BnbChainAction):
    name: str = "gas_price_trend"
    description: str = "Analyze recent blocks to determine the average gas price trend."
    args_schema: type[BaseModel] = GasPriceTrendInput
    func = get_gas_price_trend

# --------------------------------------------------------------------
# 6. Transaction Fee Estimator
# --------------------------------------------------------------------

class TransactionFeeEstimatorInput(BaseModel):
    gas_limit: int = Field(..., description="Gas limit for the transaction.")
    gas_price_gwei: int = Field(..., description="Gas price in Gwei.")

def estimate_transaction_fee(provider: BnbChainProvider, gas_limit: int, gas_price_gwei: int) -> str:
    gas_price_wei = Web3.to_wei(gas_price_gwei, 'gwei')
    fee_wei = gas_limit * gas_price_wei
    fee_bnb = Web3.from_wei(fee_wei, 'ether')
    return f"Estimated transaction fee: {fee_bnb} BNB (Gas Limit: {gas_limit}, Gas Price: {gas_price_gwei} Gwei)"

class TransactionFeeEstimatorAction(BnbChainAction):
    name: str = "transaction_fee_estimator"
    description: str = "Estimate the transaction fee based on provided gas limit and gas price."
    args_schema: type[BaseModel] = TransactionFeeEstimatorInput
    func = estimate_transaction_fee

# --------------------------------------------------------------------
# 7. Transaction Volume Analyzer
# --------------------------------------------------------------------

class TransactionVolumeAnalyzerInput(BaseModel):
    address: str = Field(..., description="Address to analyze transaction volume for.")
    hours: int = Field(24, description="Time period in hours to consider.")

def analyze_transaction_volume(provider: BnbChainProvider, address: str, hours: int = 24) -> str:
    api_key = os.environ.get("BSCSCAN_API_KEY")
    if not api_key:
        return "BSCSCAN_API_KEY not set in environment."
    current_time = int(time.time())
    from_timestamp = current_time - hours * 3600
    url = (
        f"https://api.bscscan.com/api?module=account&action=txlist&address={address}"
        f"&starttimestamp={from_timestamp}&endtimestamp={current_time}&sort=desc&apikey={api_key}"
    )
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") != "1":
            return f"Error fetching transactions: {data.get('message', 'Unknown error')}"
        txs = data.get("result", [])
        total_volume = sum(int(tx['value']) for tx in txs)
        total_volume_bnb = Web3.from_wei(total_volume, 'ether')
        count = len(txs)
        avg_volume = total_volume_bnb / count if count > 0 else 0
        return (
            f"In the last {hours} hours, address {address} has a total transaction volume of "
            f"{total_volume_bnb} BNB over {count} transactions, averaging {avg_volume} BNB per transaction."
        )
    except Exception as e:
        return f"Error analyzing transaction volume: {str(e)}"

class TransactionVolumeAnalyzerAction(BnbChainAction):
    name: str = "transaction_volume_analyzer"
    description: str = "Analyze the total transaction volume for an address over a specified time period."
    args_schema: type[BaseModel] = TransactionVolumeAnalyzerInput
    func = analyze_transaction_volume

# --------------------------------------------------------------------
# 8. Token Transfer History
# --------------------------------------------------------------------

class TokenTransferHistoryInput(BaseModel):
    address: str = Field(..., description="Address to get token transfer history for.")
    token: str = Field("BNB", description="Token symbol or contract address. Use 'BNB' for native token.")
    limit: int = Field(5, description="Number of transfers to retrieve.")

def get_token_transfer_history(provider: BnbChainProvider, address: str, token: str = "BNB", limit: int = 5) -> str:
    api_key = os.environ.get("BSCSCAN_API_KEY")
    if not api_key:
        return "BSCSCAN_API_KEY not set in environment."
    
    if token.upper() == "BNB":
        url = (
            f"https://api.bscscan.com/api?module=account&action=txlist&address={address}"
            f"&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={api_key}"
        )
    else:
        # Map token symbol to contract address if available
        contract_address = TOKEN_CONTRACT_ADDRESSES.get(token.upper(), token)
        url = (
            f"https://api.bscscan.com/api?module=account&action=tokentx&address={address}"
            f"&contractaddress={contract_address}&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={api_key}"
        )
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") != "1":
            return f"Error fetching transfer history: {data.get('message', 'Unknown error')}"
        txs = data.get("result", [])
        result = f"Token Transfer History for {token.upper()} on address {address}:\n"
        for i, tx in enumerate(txs, 1):
            value_bnb = Web3.from_wei(int(tx['value']), 'ether')
            result += f"{i}. TxHash: {tx['hash']} transferred {value_bnb} {token.upper()} at Block {tx['blockNumber']}\n"
        return result
    except Exception as e:
        return f"Error fetching token transfer history: {str(e)}"
    
class TokenTransferHistoryAction(BnbChainAction):
    name: str = "token_transfer_history"
    description: str = "Retrieve the history of token transfers for a given address and token."
    args_schema: type[BaseModel] = TokenTransferHistoryInput
    func = get_token_transfer_history
