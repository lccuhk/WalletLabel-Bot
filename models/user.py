"""
用户模型
"""

import enum
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, Float, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class UserTier(str, enum.Enum):
    FREE = "free"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    PRO = "pro"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    language_code = Column(String, default="zh")

    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)
    subscription_expires_at = Column(DateTime)

    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)

    queries_today = Column(Integer, default=0)
    last_query_reset = Column(DateTime, default=datetime.utcnow)

    invited_by = Column(Integer, index=True)
    invite_code = Column(String, unique=True, index=True)
    invite_count = Column(Integer, default=0)

    total_paid = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    queries = relationship("QueryHistory", back_populates="user")

    @property
    def is_subscription_active(self) -> bool:
        if self.tier in [UserTier.FREE, UserTier.ADMIN]:
            return True
        if self.subscription_expires_at and self.subscription_expires_at > datetime.utcnow():
            return True
        return False

    @property
    def can_query(self) -> bool:
        if not self.is_active or self.is_banned:
            return False
        if not self.is_subscription_active:
            return False
        if self.tier == UserTier.FREE:
            today = datetime.utcnow().date()
            if self.last_query_reset.date() != today:
                self.queries_today = 0
                self.last_query_reset = datetime.utcnow()
            from config import settings
            return self.queries_today < settings.FREE_DAILY_LIMIT
        return True

    @property
    def daily_limit(self) -> int:
        if self.tier == UserTier.FREE:
            from config import settings
            return settings.FREE_DAILY_LIMIT
        return 9999

    @property
    def can_analyze(self) -> bool:
        return self.tier in [UserTier.MONTHLY, UserTier.YEARLY, UserTier.PRO, UserTier.ADMIN]

    @property
    def can_batch_query(self) -> bool:
        return self.tier in [UserTier.YEARLY, UserTier.PRO, UserTier.ADMIN]

    def extend_subscription(self, days: int):
        now = datetime.utcnow()
        if self.subscription_expires_at and self.subscription_expires_at > now:
            self.subscription_expires_at = self.subscription_expires_at + timedelta(days=days)
        else:
            self.subscription_expires_at = now + timedelta(days=days)

    def increment_queries(self):
        today = datetime.utcnow().date()
        if self.last_query_reset.date() != today:
            self.queries_today = 0
            self.last_query_reset = datetime.utcnow()
        self.queries_today += 1


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    address = Column(String, nullable=False, index=True)
    query_type = Column(String, nullable=False)
    result_summary = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="queries")


def generate_invite_code() -> str:
    return f"WL{uuid.uuid4().hex[:8].upper()}"
