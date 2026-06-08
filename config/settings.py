"""
配置模块
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path if env_path.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_ID: int = 0

    DATABASE_URL: str = "sqlite:///./data/wallet_bot.db"

    ETHERSCAN_API_KEY: str = ""
    BSCSCAN_API_KEY: str = ""
    POLYGONSCAN_API_KEY: str = ""

    FREE_DAILY_LIMIT: int = 3

    PRICE_MONTHLY: float = 19.9
    PRICE_YEARLY: float = 199
    PRICE_PRO: float = 99

    TIMEZONE: str = "Asia/Shanghai"
    LOG_LEVEL: str = "INFO"

    USDT_TRC20_ADDRESS: str = ""

    @property
    def supported_chains(self) -> List[str]:
        return ["ethereum", "bsc", "polygon"]

    @property
    def address_patterns(self) -> dict:
        return {
            "ethereum": r"^0x[a-fA-F0-9]{40}$",
            "bsc": r"^0x[a-fA-F0-9]{40}$",
            "polygon": r"^0x[a-fA-F0-9]{40}$",
            "bitcoin": r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[ac-hj-np-z02-9]{39,59}$",
            "tron": r"^T[a-zA-Z0-9]{33}$",
            "solana": r"^[1-9A-HJ-NP-Za-km-z]{32,44}$",
        }


settings = Settings()
