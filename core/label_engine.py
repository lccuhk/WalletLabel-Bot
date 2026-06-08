"""
地址标签查询引擎 - 内置知名地址数据库 + 公开API查询
"""

import json
import time
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import requests

from config import settings
from models import get_db_context, AddressLabel, AddressType, RiskLevel, AddressCache


class LabelEngine:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data" / "labels"
        self.data_dir.mkdir(exist_ok=True)

        self._local_labels: Dict[str, AddressLabel] = {}
        self._load_local_labels()

        self._cache_ttl = 86400

    def _load_local_labels(self):
        self._exchange_labels = self._get_exchange_labels()
        self._known_addresses = self._get_known_addresses()

        # 将所有地址键转换为小写
        for chain in self._exchange_labels:
            self._exchange_labels[chain] = {
                k.lower(): v for k, v in self._exchange_labels[chain].items()
            }
        for chain in self._known_addresses:
            self._known_addresses[chain] = {
                k.lower(): v for k, v in self._known_addresses[chain].items()
            }

        logger.info(f"Loaded {len(self._exchange_labels)} exchange labels")
        logger.info(f"Loaded {len(self._known_addresses)} known addresses")

    def _get_exchange_labels(self) -> Dict[str, Dict]:
        return {
            "ethereum": {
                "0x28C6c06298d514Db089934071355E5743bf21d60": {
                    "name": "Binance", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0x974caa59e49682cda0ad2bbe82983419a2ecc400": {
                    "name": "Binance 2", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8": {
                    "name": "Binance 3", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3": {
                    "name": "Coinbase", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0x503828976D22510aA0d51e3d0240f8B130eE4760": {
                    "name": "Coinbase 2", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0xA090E74d50f65474b7B2c46f0d4E659472C4e92e": {
                    "name": "OKX", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0x6CC14824EaB55f4b7c2d156071867BdDf9F5d64F": {
                    "name": "OKX 2", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B": {
                    "name": "Huobi", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0xED553B6B11d74913304A81B906c0B27d1b8D28Dd": {
                    "name": "KuCoin", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0x123D1e041a41A3247d69468237f29Df2e9b5654A": {
                    "name": "Kraken", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
            },
            "bsc": {
                "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3": {
                    "name": "Binance", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0x187fA51Ff917a7F104240727713928d671C36e1F": {
                    "name": "Binance 2", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0x5BDb37d0Ddea3F30594B36ea3D6544D2660e526B": {
                    "name": "OKX", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
                "0x2358b657435E64D1d5c68d1d1d7b93D1b8D9f9b1": {
                    "name": "KuCoin", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW, "verified": True
                },
            },
        }

    def _get_known_addresses(self) -> Dict[str, Dict]:
        return {
            "ethereum": {
                "0x742d35Cc6634C0532925a3b844Bc9e7595f5bBc": {
                    "name": "Justin Sun", "type": AddressType.WHALE, "risk": RiskLevel.MEDIUM, "tags": ["tron", "huobi"]
                },
                "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8": {
                    "name": "Binance CEO", "type": AddressType.WHALE, "risk": RiskLevel.LOW, "tags": ["binance", "cz"]
                },
                "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae": {
                    "name": "Vitalik Buterin", "type": AddressType.WHALE, "risk": RiskLevel.LOW, "tags": ["ethereum", "founder"]
                },
                "0x690B9A9E9aa1C9dB991C7721a92d351Db4FaC990": {
                    "name": "FTX Hacker", "type": AddressType.HACKER, "risk": RiskLevel.CRITICAL,
                    "tags": ["hacker", "ftx", "stolen"], "description": "FTX 交易所黑客地址"
                },
                "0x73a052500105205d34daf004eab301916da8190f": {
                    "name": "Ronin Hacker", "type": AddressType.HACKER, "risk": RiskLevel.CRITICAL,
                    "tags": ["hacker", "ronin", "stolen"], "description": "Ronin 桥黑客地址"
                },
                "0x57757E3D981446D585Af0D9Ae4d7DF6D6464780": {
                    "name": "Nomad Hacker", "type": AddressType.HACKER, "risk": RiskLevel.CRITICAL,
                    "tags": ["hacker", "nomad", "stolen"], "description": "Nomad 桥黑客地址"
                },
            },
            "bsc": {
                "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3": {
                    "name": "Binance Hot Wallet", "type": AddressType.EXCHANGE, "risk": RiskLevel.LOW,
                    "tags": ["binance", "hot_wallet"]
                },
            },
        }

    def _get_scam_addresses(self) -> List[str]:
        return [
            "0x1fC83f75499b7620d53757f0b01e2e2b456b0e7e",
            "0x2e3a3a26f472d41d4c9b4e4a6951d4e3a2a4e4e4",
        ]

    def _check_local_database(self, address: str, chain: str) -> Optional[AddressLabel]:
        address_lower = address.lower()

        with get_db_context() as db:
            label = db.query(AddressLabel).filter(
                AddressLabel.address == address_lower,
                AddressLabel.chain == chain
            ).first()

            if label:
                if label.updated_at and (datetime.utcnow() - label.updated_at).total_seconds() < self._cache_ttl:
                    return label

        chain_labels = self._exchange_labels.get(chain, {})
        if address_lower in chain_labels:
            info = chain_labels[address_lower]
            return self._create_label(address, chain, info)

        chain_known = self._known_addresses.get(chain, {})
        if address_lower in chain_known:
            info = chain_known[address_lower]
            return self._create_label(address, chain, info)

        if address_lower in self._get_scam_addresses():
            return self._create_label(address, chain, {
                "name": "疑似诈骗地址",
                "type": AddressType.SCAM,
                "risk": RiskLevel.CRITICAL,
                "tags": ["scam", "high_risk"],
                "description": "该地址被标记为高风险诈骗地址，请谨慎交互"
            })

        return None

    def _create_label(self, address: str, chain: str, info: Dict) -> AddressLabel:
        with get_db_context() as db:
            label = AddressLabel(
                address=address.lower(),
                chain=chain,
                address_type=info.get("type", AddressType.UNKNOWN),
                label=info.get("name", "Unknown"),
                description=info.get("description", ""),
                risk_level=info.get("risk", RiskLevel.MEDIUM),
                risk_score=self._calculate_risk_score(info.get("risk", RiskLevel.MEDIUM)),
                tags=info.get("tags", []),
                source="local_database",
                is_verified=info.get("verified", False),
            )

            existing = db.query(AddressLabel).filter(
                AddressLabel.address == address.lower(),
                AddressLabel.chain == chain
            ).first()

            if existing:
                existing.address_type = label.address_type
                existing.label = label.label
                existing.description = label.description
                existing.risk_level = label.risk_level
                existing.risk_score = label.risk_score
                existing.tags = label.tags
                existing.is_verified = label.is_verified
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                return existing

            db.add(label)
            db.commit()
            db.refresh(label)
            return label

    def _calculate_risk_score(self, risk_level: RiskLevel) -> float:
        scores = {
            RiskLevel.LOW: 90.0,
            RiskLevel.MEDIUM: 50.0,
            RiskLevel.HIGH: 25.0,
            RiskLevel.CRITICAL: 5.0,
        }
        return scores.get(risk_level, 50.0)

    def _query_public_api(self, address: str, chain: str) -> Optional[Dict]:
        try:
            url = f"https://api.arkhamintelligence.com/intelligence/address/{address}/all"
            headers = {"Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data:
                    return self._parse_arkham_data(data, address, chain)
        except Exception as e:
            logger.debug(f"Arkham API query failed: {e}")

        try:
            url = f"https://api.dedaub.com/api/addresses/{address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and data.get("label"):
                    return self._parse_dedaub_data(data, address, chain)
        except Exception as e:
            logger.debug(f"Dedaub API query failed: {e}")

        return None

    def _parse_arkham_data(self, data: Dict, address: str, chain: str) -> Dict:
        result = {
            "name": data.get("arkhamEntity", {}).get("name") or data.get("label"),
            "type": AddressType.UNKNOWN,
            "risk": RiskLevel.MEDIUM,
            "tags": [],
            "description": "",
            "source": "arkham",
            "verified": data.get("arkhamEntity", {}).get("isVerified", False),
        }

        entity_type = data.get("arkhamEntity", {}).get("type")
        if entity_type:
            type_mapping = {
                "exchange": AddressType.EXCHANGE,
                "miner": AddressType.MINER,
                "whale": AddressType.WHALE,
                "institution": AddressType.INSTITUTION,
                "market_maker": AddressType.MARKET_MAKER,
                "hacker": AddressType.HACKER,
                "scam": AddressType.SCAM,
                "contract": AddressType.CONTRACT,
                "defi": AddressType.DEFI_PROTOCOL,
                "nft": AddressType.NFT,
                "bridge": AddressType.BRIDGE,
            }
            result["type"] = type_mapping.get(entity_type.lower(), AddressType.UNKNOWN)

        if result["type"] in [AddressType.HACKER, AddressType.SCAM, AddressType.MONEY_LAUNDERING]:
            result["risk"] = RiskLevel.CRITICAL
        elif result["type"] in [AddressType.EXCHANGE, AddressType.INSTITUTION]:
            result["risk"] = RiskLevel.LOW
        elif result["type"] in [AddressType.WHALE, AddressType.MARKET_MAKER]:
            result["risk"] = RiskLevel.MEDIUM

        description = data.get("arkhamEntity", {}).get("description")
        if description:
            result["description"] = description

        tags = data.get("arkhamEntity", {}).get("tags", [])
        if tags:
            result["tags"] = tags

        return result

    def _parse_dedaub_data(self, data: Dict, address: str, chain: str) -> Dict:
        return {
            "name": data.get("label"),
            "type": AddressType.UNKNOWN,
            "risk": RiskLevel.MEDIUM,
            "tags": data.get("tags", []),
            "description": data.get("notes", ""),
            "source": "dedaub",
            "verified": False,
        }

    def _analyze_address_pattern(self, address: str, chain: str, blockchain_info: Dict) -> Dict:
        result = {
            "name": None,
            "type": AddressType.UNKNOWN,
            "risk": RiskLevel.MEDIUM,
            "tags": [],
            "description": "",
            "source": "pattern_analysis",
            "verified": False,
        }

        address_type = blockchain_info.get("address_type")
        if address_type == "contract":
            result["type"] = AddressType.CONTRACT
            result["name"] = "合约地址"
            result["description"] = "这是一个智能合约地址"
            result["tags"].append("contract")

        elif address_type == "burn":
            result["type"] = AddressType.CONTRACT
            result["name"] = "燃烧地址"
            result["risk"] = RiskLevel.LOW
            result["description"] = "这是一个代币燃烧地址"
            result["tags"].append("burn")

        else:
            tx_count = blockchain_info.get("transaction_count", 0)
            balance = blockchain_info.get("native_balance", 0)

            if tx_count == 0 and balance == 0:
                result["type"] = AddressType.UNKNOWN
                result["name"] = "新地址"
                result["description"] = "该地址没有交易记录，可能是新创建的地址"
                result["tags"].append("new_address")
                result["risk"] = RiskLevel.HIGH

            elif tx_count < 5:
                result["type"] = AddressType.REGULAR_USER
                result["name"] = "新用户地址"
                result["description"] = "该地址交易次数较少，请谨慎交互"
                result["tags"].append("low_activity")
                result["risk"] = RiskLevel.HIGH

            elif balance > 1000:
                result["type"] = AddressType.WHALE
                result["name"] = "大户地址"
                result["description"] = f"该地址持有大量 {blockchain_info.get('native_symbol', 'ETH')}"
                result["tags"].append("whale")
                result["risk"] = RiskLevel.MEDIUM

            elif tx_count > 1000:
                result["type"] = AddressType.REGULAR_USER
                result["name"] = "活跃用户"
                result["description"] = "该地址交易频繁，可能是活跃交易者"
                result["tags"].append("active_trader")
                result["risk"] = RiskLevel.MEDIUM

            else:
                result["type"] = AddressType.REGULAR_USER
                result["name"] = "普通用户地址"
                result["description"] = "这是一个普通用户地址"
                result["tags"].append("regular_user")
                result["risk"] = RiskLevel.MEDIUM

            error_rate = blockchain_info.get("error_rate", 0)
            if error_rate > 0.3:
                result["tags"].append("high_error_rate")
                if result["risk"] == RiskLevel.MEDIUM:
                    result["risk"] = RiskLevel.HIGH
                result["description"] += f" 该地址交易失败率较高 ({error_rate:.1%})"

        return result

    def get_label(self, address: str, chain: str = None, blockchain_info: Dict = None) -> AddressLabel:
        address = address.strip()
        if not chain:
            chain = blockchain_api.detect_chain(address) or "ethereum"

        local_label = self._check_local_database(address, chain)
        if local_label and local_label.is_verified:
            logger.info(f"Found local verified label for {address}: {local_label.label}")
            return local_label

        api_data = self._query_public_api(address, chain)
        if api_data and api_data.get("name"):
            label = self._create_label(address, chain, api_data)
            logger.info(f"Found API label for {address}: {label.label}")
            return label

        if local_label:
            logger.info(f"Using local label for {address}: {local_label.label}")
            return local_label

        if blockchain_info:
            pattern_data = self._analyze_address_pattern(address, chain, blockchain_info)
            label = self._create_label(address, chain, pattern_data)
            logger.info(f"Generated pattern label for {address}: {label.label}")
            return label

        return self._create_label(address, chain, {
            "name": "未知地址",
            "type": AddressType.UNKNOWN,
            "risk": RiskLevel.MEDIUM,
            "tags": ["unknown"],
            "description": "未找到该地址的标签信息"
        })

    def search_labels(self, keyword: str) -> List[AddressLabel]:
        keyword = keyword.lower()
        with get_db_context() as db:
            labels = db.query(AddressLabel).filter(
                (AddressLabel.label.ilike(f"%{keyword}%")) |
                (AddressLabel.address.ilike(f"%{keyword}%"))
            ).limit(20).all()
            return labels

    def get_stats(self) -> Dict:
        with get_db_context() as db:
            total_labels = db.query(AddressLabel).count()
            verified_labels = db.query(AddressLabel).filter(AddressLabel.is_verified == True).count()
            type_counts = {}
            for addr_type in AddressType:
                count = db.query(AddressLabel).filter(AddressLabel.address_type == addr_type).count()
                if count > 0:
                    type_counts[addr_type.value] = count

            return {
                "total_labels": total_labels,
                "verified_labels": verified_labels,
                "type_counts": type_counts,
            }


label_engine = LabelEngine()
