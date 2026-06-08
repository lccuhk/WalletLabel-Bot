"""
持仓分析引擎 - 分析地址的持仓和交易行为
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta
from loguru import logger

from models import get_db_context, AddressCache
from .blockchain_api import blockchain_api


class AnalysisEngine:
    def __init__(self):
        self._cache_ttl = 3600

    def analyze_address(self, address: str, chain: str = None) -> Dict:
        if not chain:
            chain = blockchain_api.detect_chain(address) or "ethereum"

        address_lower = address.lower()

        with get_db_context() as db:
            cache = db.query(AddressCache).filter(
                AddressCache.address == address_lower,
                AddressCache.chain == chain
            ).first()

            if cache and not cache.is_expired:
                logger.info(f"Using cached analysis for {address}")
                return self._format_analysis_result(cache)

        logger.info(f"Analyzing address: {address} on {chain}")

        blockchain_info = blockchain_api.get_address_info(address, chain)

        result = {
            "address": address,
            "chain": chain,
            "chain_name": blockchain_info.get("chain_name", chain),
            "blockchain_info": blockchain_info,
            "holdings_analysis": self._analyze_holdings(blockchain_info),
            "transaction_analysis": self._analyze_transactions(blockchain_info),
            "behavior_analysis": self._analyze_behavior(blockchain_info),
        }

        self._save_to_cache(address_lower, chain, blockchain_info, result)

        return result

    def _analyze_holdings(self, blockchain_info: Dict) -> Dict:
        result = {
            "native_balance": blockchain_info.get("native_balance", 0),
            "native_symbol": blockchain_info.get("native_symbol", ""),
            "token_count": blockchain_info.get("token_count", 0),
            "tokens": [],
            "diversification_score": 0,
            "holding_summary": "",
        }

        tokens = blockchain_info.get("tokens", [])
        if tokens:
            tokens_sorted = sorted(tokens, key=lambda x: x.get("balance", 0), reverse=True)
            result["tokens"] = tokens_sorted[:10]

            non_zero_tokens = [t for t in tokens if t.get("balance", 0) > 0]
            if len(non_zero_tokens) > 5:
                result["diversification_score"] = 80
                result["holding_summary"] = "持仓分散，持有多种代币"
            elif len(non_zero_tokens) > 2:
                result["diversification_score"] = 50
                result["holding_summary"] = "持仓较为集中，持有少量代币"
            else:
                result["diversification_score"] = 20
                result["holding_summary"] = "持仓高度集中"

        native_balance = blockchain_info.get("native_balance", 0)
        if native_balance > 100:
            result["holding_summary"] += f"，持有大量 {result['native_symbol']}"
        elif native_balance > 10:
            result["holding_summary"] += f"，持有适量 {result['native_symbol']}"
        elif native_balance > 1:
            result["holding_summary"] += f"，持有少量 {result['native_symbol']}"
        else:
            result["holding_summary"] += f"，{result['native_symbol']} 余额较低"

        return result

    def _analyze_transactions(self, blockchain_info: Dict) -> Dict:
        result = {
            "total_transactions": blockchain_info.get("transaction_count", 0),
            "sent_count": blockchain_info.get("sent_count", 0),
            "received_count": blockchain_info.get("received_count", 0),
            "total_sent": blockchain_info.get("total_sent", 0),
            "total_received": blockchain_info.get("total_received", 0),
            "first_transaction": blockchain_info.get("first_transaction"),
            "last_transaction": blockchain_info.get("last_transaction"),
            "error_rate": blockchain_info.get("error_rate", 0),
            "activity_level": "inactive",
            "transaction_summary": "",
            "age_days": 0,
            "tx_per_day": 0,
        }

        tx_count = result["total_transactions"]
        first_tx = result["first_transaction"]
        last_tx = result["last_transaction"]

        if first_tx and last_tx:
            age_days = (last_tx - first_tx).days
            result["age_days"] = age_days
            if age_days > 0:
                result["tx_per_day"] = round(tx_count / age_days, 2)

            if age_days > 365:
                result["transaction_summary"] += f"地址已活跃 {age_days // 365} 年"
            elif age_days > 30:
                result["transaction_summary"] += f"地址已活跃 {age_days // 30} 个月"
            else:
                result["transaction_summary"] += f"地址已活跃 {age_days} 天"

        if tx_count > 1000:
            result["activity_level"] = "very_active"
            result["transaction_summary"] += "，交易非常活跃"
        elif tx_count > 100:
            result["activity_level"] = "active"
            result["transaction_summary"] += "，交易较为活跃"
        elif tx_count > 10:
            result["activity_level"] = "moderate"
            result["transaction_summary"] += "，交易活跃度一般"
        else:
            result["activity_level"] = "inactive"
            result["transaction_summary"] += "，交易活跃度较低"

        if result["error_rate"] > 0.3:
            result["transaction_summary"] += f"，交易失败率较高 ({result['error_rate']:.1%})"

        if result["sent_count"] > result["received_count"] * 2:
            result["transaction_summary"] += "，以转出为主"
        elif result["received_count"] > result["sent_count"] * 2:
            result["transaction_summary"] += "，以转入为主"

        return result

    def _analyze_behavior(self, blockchain_info: Dict) -> Dict:
        result = {
            "behavior_type": "unknown",
            "behavior_description": "",
            "risk_factors": [],
            "positive_factors": [],
            "trust_score": 50,
        }

        tx_count = blockchain_info.get("transaction_count", 0)
        error_rate = blockchain_info.get("error_rate", 0)
        first_tx = blockchain_info.get("first_transaction")
        last_tx = blockchain_info.get("last_transaction")

        if tx_count == 0:
            result["behavior_type"] = "new_address"
            result["behavior_description"] = "该地址没有任何交易记录，可能是新创建的地址"
            result["risk_factors"].append("新地址，无历史记录")
            result["trust_score"] = 10

        elif tx_count < 5:
            result["behavior_type"] = "low_activity"
            result["behavior_description"] = "该地址交易次数很少，可能是不常用地址或新地址"
            result["risk_factors"].append("交易记录少，难以评估信用")
            result["trust_score"] = 30

        else:
            if first_tx and (datetime.utcnow() - first_tx).days > 365:
                result["positive_factors"].append("地址历史悠久")
                result["trust_score"] += 20

            if last_tx and (datetime.utcnow() - last_tx).days < 30:
                result["positive_factors"].append("近期活跃")
                result["trust_score"] += 10

            if error_rate < 0.1:
                result["positive_factors"].append("交易成功率高")
                result["trust_score"] += 10
            elif error_rate > 0.3:
                result["risk_factors"].append("交易失败率高")
                result["trust_score"] -= 15

            sent_count = blockchain_info.get("sent_count", 0)
            received_count = blockchain_info.get("received_count", 0)
            total_sent = blockchain_info.get("total_sent", 0)
            total_received = blockchain_info.get("total_received", 0)

            if total_received > total_sent * 10 and tx_count > 50:
                result["behavior_type"] = "accumulator"
                result["behavior_description"] = "该地址主要是只进不出，可能是长期持有者"
                result["positive_factors"].append("长期持有者")
                result["trust_score"] += 10
            elif abs(sent_count - received_count) < 10 and tx_count > 100:
                result["behavior_type"] = "trader"
                result["behavior_description"] = "该地址交易频繁，可能是活跃交易者"
                result["positive_factors"].append("活跃交易者")
            elif sent_count > received_count * 3 and total_sent > total_received * 2:
                result["behavior_type"] = "distributor"
                result["behavior_description"] = "该地址主要是向外转账，可能是分发地址"
                result["risk_factors"].append("大量向外转账")
            else:
                result["behavior_type"] = "regular_user"
                result["behavior_description"] = "该地址行为模式符合普通用户特征"

        result["trust_score"] = max(0, min(100, result["trust_score"]))

        return result

    def _format_analysis_result(self, cache: AddressCache) -> Dict:
        return {
            "address": cache.address,
            "chain": cache.chain,
            "blockchain_info": {
                "native_balance": cache.balance,
                "transaction_count": cache.transaction_count,
                "first_transaction": cache.first_transaction,
                "last_transaction": cache.last_transaction,
                "tokens": cache.token_holdings,
            },
            "holdings_analysis": cache.analysis_result.get("holdings_analysis", {}) if cache.analysis_result else {},
            "transaction_analysis": cache.analysis_result.get("transaction_analysis", {}) if cache.analysis_result else {},
            "behavior_analysis": cache.analysis_result.get("behavior_analysis", {}) if cache.analysis_result else {},
            "cached": True,
            "cached_at": cache.cached_at,
        }

    def _save_to_cache(self, address: str, chain: str, blockchain_info: Dict, analysis: Dict):
        with get_db_context() as db:
            cache = db.query(AddressCache).filter(
                AddressCache.address == address,
                AddressCache.chain == chain
            ).first()

            expires_at = datetime.utcnow() + timedelta(seconds=self._cache_ttl)

            if cache:
                cache.balance = blockchain_info.get("native_balance")
                cache.transaction_count = blockchain_info.get("transaction_count")
                cache.first_transaction = blockchain_info.get("first_transaction")
                cache.last_transaction = blockchain_info.get("last_transaction")
                cache.token_holdings = blockchain_info.get("tokens")
                cache.analysis_result = analysis
                cache.query_count += 1
                cache.cached_at = datetime.utcnow()
                cache.expires_at = expires_at
            else:
                cache = AddressCache(
                    address=address,
                    chain=chain,
                    balance=blockchain_info.get("native_balance"),
                    transaction_count=blockchain_info.get("transaction_count"),
                    first_transaction=blockchain_info.get("first_transaction"),
                    last_transaction=blockchain_info.get("last_transaction"),
                    token_holdings=blockchain_info.get("tokens"),
                    analysis_result=analysis,
                    expires_at=expires_at,
                )
                db.add(cache)

            db.commit()

    def batch_analyze(self, addresses: List[str], chain: str = None) -> List[Dict]:
        results = []
        for address in addresses:
            try:
                result = self.analyze(address.strip(), chain)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {address}: {e}")
                results.append({"address": address, "error": str(e)})
        return results


analysis_engine = AnalysisEngine()
