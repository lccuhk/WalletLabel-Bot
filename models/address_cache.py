"""
地址缓存和标签模型
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum, JSON, Boolean, Text

from .database import Base


class AddressType(str, enum.Enum):
    EXCHANGE = "exchange"
    WHALE = "whale"
    INSTITUTION = "institution"
    MARKET_MAKER = "market_maker"
    HACKER = "hacker"
    SCAM = "scam"
    MONEY_LAUNDERING = "money_laundering"
    CONTRACT = "contract"
    DEFI_PROTOCOL = "defi_protocol"
    NFT = "nft"
    MINER = "miner"
    BRIDGE = "bridge"
    REGULAR_USER = "regular_user"
    UNKNOWN = "unknown"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AddressLabel(Base):
    __tablename__ = "address_labels"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    chain = Column(String, index=True, nullable=False)

    address_type = Column(Enum(AddressType), default=AddressType.UNKNOWN)
    label = Column(String, index=True)
    description = Column(Text)

    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)
    risk_score = Column(Float, default=50.0)

    tags = Column(JSON)
    extra_data = Column(JSON)

    source = Column(String)
    is_verified = Column(Boolean, default=False)

    first_seen = Column(DateTime)
    last_active = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def risk_emoji(self) -> str:
        emojis = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴",
        }
        return emojis.get(self.risk_level, "⚪")

    @property
    def type_emoji(self) -> str:
        emojis = {
            AddressType.EXCHANGE: "🏦",
            AddressType.WHALE: "🐋",
            AddressType.INSTITUTION: "🏢",
            AddressType.MARKET_MAKER: "💹",
            AddressType.HACKER: "👾",
            AddressType.SCAM: "⚠️",
            AddressType.MONEY_LAUNDERING: "💀",
            AddressType.CONTRACT: "📜",
            AddressType.DEFI_PROTOCOL: "🔷",
            AddressType.NFT: "🎨",
            AddressType.MINER: "⛏️",
            AddressType.BRIDGE: "🌉",
            AddressType.REGULAR_USER: "👤",
            AddressType.UNKNOWN: "❓",
        }
        return emojis.get(self.address_type, "❓")

    @property
    def type_name_cn(self) -> str:
        names = {
            AddressType.EXCHANGE: "交易所",
            AddressType.WHALE: "鲸鱼大户",
            AddressType.INSTITUTION: "投资机构",
            AddressType.MARKET_MAKER: "做市商",
            AddressType.HACKER: "黑客地址",
            AddressType.SCAM: "诈骗地址",
            AddressType.MONEY_LAUNDERING: "洗钱地址",
            AddressType.CONTRACT: "合约地址",
            AddressType.DEFI_PROTOCOL: "DeFi协议",
            AddressType.NFT: "NFT地址",
            AddressType.MINER: "矿工地址",
            AddressType.BRIDGE: "跨链桥",
            AddressType.REGULAR_USER: "普通用户",
            AddressType.UNKNOWN: "未知地址",
        }
        return names.get(self.address_type, "未知")

    @property
    def risk_name_cn(self) -> str:
        names = {
            RiskLevel.LOW: "低风险",
            RiskLevel.MEDIUM: "中风险",
            RiskLevel.HIGH: "较高风险",
            RiskLevel.CRITICAL: "高风险",
        }
        return names.get(self.risk_level, "未知")


class AddressCache(Base):
    __tablename__ = "address_cache"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    chain = Column(String, index=True, nullable=False)

    balance = Column(Float)
    balance_usd = Column(Float)
    transaction_count = Column(Integer)
    first_transaction = Column(DateTime)
    last_transaction = Column(DateTime)

    token_holdings = Column(JSON)
    nft_holdings = Column(JSON)
    defi_positions = Column(JSON)

    analysis_result = Column(JSON)
    risk_assessment = Column(JSON)

    query_count = Column(Integer, default=1)
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        return datetime.utcnow() > self.expires_at

    @property
    def age_days(self) -> int:
        if not self.first_transaction:
            return 0
        return (datetime.utcnow() - self.first_transaction).days

    @property
    def activity_level(self) -> str:
        if not self.transaction_count or not self.age_days:
            return "inactive"
        tx_per_day = self.transaction_count / max(self.age_days, 1)
        if tx_per_day > 10:
            return "very_active"
        elif tx_per_day > 1:
            return "active"
        elif tx_per_day > 0.1:
            return "moderate"
        else:
            return "inactive"
