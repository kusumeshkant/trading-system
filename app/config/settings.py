from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    # App
    app_env: Literal["development", "paper", "live"] = "development"
    app_name: str = "TradingSystem"
    app_port: int = 8000
    secret_key: str = "change_this"

    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    # Binance
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True

    # Angel One
    angelone_api_key: str = ""
    angelone_client_id: str = ""
    angelone_password: str = ""
    angelone_totp_secret: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Risk
    max_daily_loss_percent: float = 5.0
    max_position_size_percent: float = 10.0
    max_open_trades: int = 3
    default_leverage: int = 5

    # Email (optional — for report delivery)
    email_host: str = ""
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_to: str = ""

    # Logging
    log_level: str = "INFO"
    log_file: str = "app/logs/trading.log"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
