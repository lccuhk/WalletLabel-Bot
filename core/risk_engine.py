"""
风险评级引擎 - 综合评估地址风险等级
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from loguru import logger

from models import AddressLabel, AddressType, RiskLevel
from .blockchain_api import blockchain_api
from .label_engine import label_engine


class RiskEngine:
    def __init__(self):
        self.risk_factors = {
            "hacker_address": {"weight": 50, "description": "黑客地址"},
            "scam_address": {"weight": 50, "description": "诈骗地址"},
            "money_laundering": {"weight": 45, "description": "洗钱地址"},
            "high_error_rate": {"weight": 20, "description": "交易失败率高"},
            "new_address": {"weight": 15, "description": "新地址，无历史记录"},
            "low_activity": {"weight": 10, "description": "交易活跃度低"},
            "high_transfer_volume": {"weight": 15, "description": "大量向外转账"},
            "mixing_service": {"weight": 40, "description": "混币服务关联"},
            "sanctioned": {"weight": 50, "description": "被制裁地址"},
            "verified_exchange": {"weight": -30, "description": "知名交易所"},
            "long_history": {"weight": -15, "description": "历史悠久"},
            "high_activity": {"weight": -10, "description": "交易活跃"},
            "verified_entity": {"weight": -20, "description": "已认证实体"},
        }

    def assess_risk(self, address: str, chain: str = None,
                    label: AddressLabel = None,
                    blockchain_info: Dict = None,
                    analysis: Dict = None) -> Dict:
        if not chain:
            chain = blockchain_api.detect_chain(address) or "ethereum"

        if not label:
            label = label_engine.get_label(address, chain, blockchain_info)

        if not blockchain_info:
            blockchain_info = blockchain_api.get_address_info(address, chain)

        if not analysis:
            from .analysis_engine import analysis_engine
            analysis = analysis_engine.analyze_address(address, chain)

        risk_score = label.risk_score
        risk_factors = []
        positive_factors = []

        # 检查是否是已验证的可信实体
        is_trusted_verified = (
            label.is_verified and
            label.address_type in [
                AddressType.EXCHANGE,
                AddressType.INSTITUTION,
                AddressType.DEFI_PROTOCOL,
            ]
        )

        if label.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            risk_factors.append(f"{label.risk_emoji} {label.description or label.label}")

        if label.risk_level == RiskLevel.LOW and label.is_verified:
            positive_factors.append(f"✅ {label.label} - 已认证实体")

        if label.address_type == AddressType.EXCHANGE and label.is_verified:
            risk_score = min(100, risk_score + 30)
            positive_factors.append(self.risk_factors["verified_exchange"]["description"])

        if label.address_type in [AddressType.HACKER, AddressType.SCAM, AddressType.MONEY_LAUNDERING]:
            risk_score = max(0, risk_score - 40)
            risk_factors.append(self.risk_factors["hacker_address" if label.address_type == AddressType.HACKER else "scam_address"]["description"])

        tx_count = blockchain_info.get("transaction_count", 0)
        first_tx = blockchain_info.get("first_transaction")
        error_rate = blockchain_info.get("error_rate", 0)

        # 对于已验证的可信实体，跳过交易数据的惩罚
        if not is_trusted_verified:
            if tx_count == 0:
                risk_score = max(0, risk_score - 15)
                risk_factors.append(self.risk_factors["new_address"]["description"])
            elif tx_count < 5:
                risk_score = max(0, risk_score - 10)
                risk_factors.append(self.risk_factors["low_activity"]["description"])
            elif tx_count > 1000:
                risk_score = min(100, risk_score + 10)
                positive_factors.append(self.risk_factors["high_activity"]["description"])

            if first_tx and (datetime.utcnow() - first_tx).days > 365:
                risk_score = min(100, risk_score + 15)
                positive_factors.append(self.risk_factors["long_history"]["description"])

            if error_rate > 0.3:
                risk_score = max(0, risk_score - 20)
                risk_factors.append(f"{self.risk_factors['high_error_rate']['description']} ({error_rate:.1%})")

            sent_count = blockchain_info.get("sent_count", 0)
            received_count = blockchain_info.get("received_count", 0)
            total_sent = blockchain_info.get("total_sent", 0)
            total_received = blockchain_info.get("total_received", 0)

            if sent_count > received_count * 3 and total_sent > total_received * 2 and tx_count > 50:
                risk_score = max(0, risk_score - 15)
                risk_factors.append(self.risk_factors["high_transfer_volume"]["description"])
        else:
            # 已验证的可信实体，直接添加积极因素
            positive_factors.append("已验证实体，跳过交易数据检查")

        if label.is_verified and label.address_type in [AddressType.EXCHANGE, AddressType.INSTITUTION]:
            risk_score = min(100, risk_score + 20)
            positive_factors.append(self.risk_factors["verified_entity"]["description"])

        risk_score = max(0, min(100, risk_score))

        if risk_score >= 85:
            risk_level = RiskLevel.LOW
        elif risk_score >= 60:
            risk_level = RiskLevel.MEDIUM
        elif risk_score >= 30:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        behavior = analysis.get("behavior_analysis", {}) if analysis else {}
        trust_score = behavior.get("trust_score", 50)

        # 对于已验证的可信实体，提高标签风险的权重
        if is_trusted_verified:
            final_score = (risk_score * 0.8 + trust_score * 0.2)
        else:
            final_score = (risk_score * 0.6 + trust_score * 0.4)

        if final_score >= 85:
            final_level = RiskLevel.LOW
        elif final_score >= 60:
            final_level = RiskLevel.MEDIUM
        elif final_score >= 30:
            final_level = RiskLevel.HIGH
        else:
            final_level = RiskLevel.CRITICAL

        level_emojis = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴",
        }

        level_names = {
            RiskLevel.LOW: "低风险",
            RiskLevel.MEDIUM: "中风险",
            RiskLevel.HIGH: "较高风险",
            RiskLevel.CRITICAL: "高风险",
        }

        recommendations = self._generate_recommendations(final_level, risk_factors, positive_factors)

        return {
            "address": address,
            "chain": chain,
            "risk_score": round(final_score, 1),
            "risk_level": final_level,
            "risk_emoji": level_emojis[final_level],
            "risk_name": level_names[final_level],
            "label_risk_score": label.risk_score,
            "trust_score": trust_score,
            "risk_factors": risk_factors,
            "positive_factors": positive_factors,
            "recommendations": recommendations,
            "summary": self._generate_summary(final_level, label, risk_factors, positive_factors),
        }

    def _generate_recommendations(self, risk_level: RiskLevel,
                                    risk_factors: List[str],
                                    positive_factors: List[str]) -> List[str]:
        recommendations = []

        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("⚠️ 强烈建议不要与该地址进行任何交互")
            recommendations.append("🔴 该地址存在严重风险，可能是黑客或诈骗地址")
            recommendations.append("📢 如已发生交易，请立即联系相关平台冻结资产")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("⚠️ 建议谨慎与该地址交互")
            recommendations.append("🔍 请仔细核实对方身份，避免直接转账")
            recommendations.append("💰 建议先小额测试，确认无误后再进行大额交易")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("⚠️ 该地址风险一般，请保持警惕")
            recommendations.append("🔍 建议核实对方身份后再进行交易")
            recommendations.append("💡 可以先小额交互，逐步建立信任")
        else:
            recommendations.append("✅ 该地址风险较低")
            recommendations.append("💡 但仍需保持基本的安全意识")
            recommendations.append("🔐 永远不要泄露你的私钥或助记词")

        if risk_factors:
            recommendations.append(f"\n⚠️ 风险因素:")
            for factor in risk_factors[:3]:
                recommendations.append(f"   • {factor}")

        if positive_factors:
            recommendations.append(f"\n✅ 积极因素:")
            for factor in positive_factors[:3]:
                recommendations.append(f"   • {factor}")

        return recommendations

    def _generate_summary(self, risk_level: RiskLevel, label: AddressLabel,
                          risk_factors: List[str], positive_factors: List[str]) -> str:
        if risk_level == RiskLevel.CRITICAL:
            return f"🔴 高风险地址！{label.label}。{label.description or '该地址被标记为高风险，请谨慎交互。'}"
        elif risk_level == RiskLevel.HIGH:
            return f"🟠 较高风险地址。{label.label}。建议谨慎交互，仔细核实对方身份。"
        elif risk_level == RiskLevel.MEDIUM:
            return f"🟡 中等风险地址。{label.label}。请保持警惕，建议核实后再进行交易。"
        else:
            if label.is_verified:
                return f"🟢 低风险地址。{label.label}（已认证）。该地址风险较低。"
            else:
                return f"🟢 低风险地址。{label.label}。该地址风险较低，但仍需保持安全意识。"

    def batch_assess(self, addresses: List[str], chain: str = None) -> List[Dict]:
        results = []
        for address in addresses:
            try:
                result = self.assess_risk(address.strip(), chain)
                results.append(result)
            except Exception as e:
                logger.error(f"Error assessing risk for {address}: {e}")
                results.append({"address": address, "error": str(e)})
        return results

    def get_risk_stats(self) -> Dict:
        from models import get_db_context, AddressLabel

        with get_db_context() as db:
            total = db.query(AddressLabel).count()
            low = db.query(AddressLabel).filter(AddressLabel.risk_level == RiskLevel.LOW).count()
            medium = db.query(AddressLabel).filter(AddressLabel.risk_level == RiskLevel.MEDIUM).count()
            high = db.query(AddressLabel).filter(AddressLabel.risk_level == RiskLevel.HIGH).count()
            critical = db.query(AddressLabel).filter(AddressLabel.risk_level == RiskLevel.CRITICAL).count()

            return {
                "total": total,
                "low": low,
                "medium": medium,
                "high": high,
                "critical": critical,
                "low_percent": round(low / total * 100, 1) if total > 0 else 0,
                "medium_percent": round(medium / total * 100, 1) if total > 0 else 0,
                "high_percent": round(high / total * 100, 1) if total > 0 else 0,
                "critical_percent": round(critical / total * 100, 1) if total > 0 else 0,
            }


risk_engine = RiskEngine()
