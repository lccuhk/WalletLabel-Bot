"""
区块链 API 封装 - 支持多链查询
"""

import time
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from loguru import logger
import requests

from config import settings


class BlockchainAPI:
    def __init__(self):
        self.etherscan_key = settings.ETHERSCAN_API_KEY
        self.bscscan_key = settings.BSCSCAN_API_KEY
        self.polygonscan_key = settings.POLYGONSCAN_API_KEY

        self._cache: Dict[str, Tuple[Dict, float]] = {}
        self._cache_ttl = 300

        self.chain_configs = {
            "ethereum": {
                "name": "以太坊",
                "symbol": "ETH",
                "scan_url": "https://api.etherscan.io/api",
                "api_key": self.etherscan_key,
                "explorer_url": "https://etherscan.io",
            },
            "bsc": {
                "name": "币安智能链",
                "symbol": "BNB",
                "scan_url": "https://api.bscscan.com/api",
                "api_key": self.bscscan_key,
                "explorer_url": "https://bscscan.com",
            },
            "polygon": {
                "name": "Polygon",
                "symbol": "MATIC",
                "scan_url": "https://api.polygonscan.com/api",
                "api_key": self.polygonscan_key,
                "explorer_url": "https://polygonscan.com",
            },
        }

    def detect_chain(self, address: str) -> Optional[str]:
        address = address.strip()

        patterns = settings.address_patterns

        if re.match(patterns["ethereum"], address):
            return "ethereum"
        elif re.match(patterns["bitcoin"], address):
            return "bitcoin"
        elif re.match(patterns["tron"], address):
            return "tron"
        elif re.match(patterns["solana"], address):
            return "solana"

        return None

    def detect_address_type(self, address: str, chain: str = None) -> str:
        if not chain:
            chain = self.detect_chain(address)

        if chain in ["ethereum", "bsc", "polygon"]:
            if address.endswith("0000000000000000000000000000000000000000"):
                return "burn"
            if address.lower() == address:
                return "contract"
            return "eoa"

        return "unknown"

    def _get_cached(self, key: str) -> Optional[Dict]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
        return None

    def _set_cache(self, key: str, data: Dict):
        self._cache[key] = (data, time.time())

    def get_balance(self, address: str, chain: str = "ethereum") -> Optional[float]:
        cache_key = f"balance_{chain}_{address}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached.get("balance")

        config = self.chain_configs.get(chain)
        if not config:
            return None

        try:
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
            }
            if config["api_key"]:
                params["apikey"] = config["api_key"]

            response = requests.get(config["scan_url"], params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    balance_wei = int(data.get("result", "0"))
                    balance = balance_wei / 10**18
                    self._set_cache(cache_key, {"balance": balance})
                    return balance
        except Exception as e:
            logger.warning(f"Error getting {chain} balance for {address}: {e}")

        return None

    def get_transactions(self, address: str, chain: str = "ethereum", limit: int = 100) -> Optional[List[Dict]]:
        cache_key = f"txs_{chain}_{address}_{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached.get("transactions")

        config = self.chain_configs.get(chain)
        if not config:
            return None

        try:
            params = {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": limit,
                "sort": "desc",
            }
            if config["api_key"]:
                params["apikey"] = config["api_key"]

            response = requests.get(config["scan_url"], params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    transactions = []
                    for tx in data.get("result", []):
                        transactions.append({
                            "hash": tx.get("hash"),
                            "from": tx.get("from"),
                            "to": tx.get("to"),
                            "value": int(tx.get("value", "0")) / 10**18,
                            "gas_price": int(tx.get("gasPrice", "0")) / 10**9,
                            "timestamp": int(tx.get("timeStamp", "0")),
                            "block_number": int(tx.get("blockNumber", "0")),
                            "is_error": tx.get("isError") == "1",
                            "confirmations": int(tx.get("confirmations", "0")),
                        })
                    self._set_cache(cache_key, {"transactions": transactions})
                    return transactions
        except Exception as e:
            logger.warning(f"Error getting {chain} transactions for {address}: {e}")

        return None

    def get_token_balances(self, address: str, chain: str = "ethereum") -> Optional[List[Dict]]:
        cache_key = f"tokens_{chain}_{address}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached.get("tokens")

        config = self.chain_configs.get(chain)
        if not config:
            return None

        try:
            params = {
                "module": "account",
                "action": "tokenlist",
                "address": address,
            }
            if config["api_key"]:
                params["apikey"] = config["api_key"]

            response = requests.get(config["scan_url"], params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    tokens = []
                    for token in data.get("result", []):
                        balance = int(token.get("balance", "0"))
                        decimals = int(token.get("decimals", "18"))
                        tokens.append({
                            "symbol": token.get("symbol"),
                            "name": token.get("name"),
                            "contract_address": token.get("contractAddress"),
                            "balance": balance / 10**decimals,
                            "decimals": decimals,
                            "type": token.get("type"),
                        })
                    self._set_cache(cache_key, {"tokens": tokens})
                    return tokens
        except Exception as e:
            logger.warning(f"Error getting {chain} token balances for {address}: {e}")

        return None

    def get_address_info(self, address: str, chain: str = None) -> Dict:
        if not chain:
            chain = self.detect_chain(address) or "ethereum"

        config = self.chain_configs.get(chain, {})

        result = {
            "address": address,
            "chain": chain,
            "chain_name": config.get("name", chain),
            "address_type": self.detect_address_type(address, chain),
            "native_balance": 0.0,
            "native_symbol": config.get("symbol", ""),
            "transaction_count": 0,
            "token_count": 0,
            "tokens": [],
            "sent_count": 0,
            "received_count": 0,
            "total_sent": 0.0,
            "total_received": 0.0,
            "error_rate": 0.0,
        }

        balance = self.get_balance(address, chain)
        if balance is not None:
            result["native_balance"] = balance

        transactions = self.get_transactions(address, chain, limit=100)
        if transactions:
            result["transaction_count"] = len(transactions)
            if transactions:
                result["first_transaction"] = datetime.fromtimestamp(transactions[-1]["timestamp"])
                result["last_transaction"] = datetime.fromtimestamp(transactions[0]["timestamp"])

                sent_count = sum(1 for tx in transactions if tx["from"].lower() == address.lower())
                received_count = sum(1 for tx in transactions if tx["to"].lower() == address.lower())
                result["sent_count"] = sent_count
                result["received_count"] = received_count

                total_sent = sum(tx["value"] for tx in transactions if tx["from"].lower() == address.lower())
                total_received = sum(tx["value"] for tx in transactions if tx["to"].lower() == address.lower())
                result["total_sent"] = total_sent
                result["total_received"] = total_received

                error_count = sum(1 for tx in transactions if tx["is_error"])
                result["error_rate"] = error_count / len(transactions) if transactions else 0

        tokens = self.get_token_balances(address, chain)
        if tokens:
            result["token_count"] = len(tokens)
            result["tokens"] = tokens[:20]

        return result

    def get_explorer_url(self, address: str, chain: str = "ethereum") -> str:
        config = self.chain_configs.get(chain)
        if config:
            return f"{config['explorer_url']}/address/{address}"
        return f"https://etherscan.io/address/{address}"


blockchain_api = BlockchainAPI()
