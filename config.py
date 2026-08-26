"""
Configuration manager loading environment variables safely.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current working directory or parent directories
load_dotenv()


@dataclass(frozen=True)
class Config:
    # Meta WhatsApp API
    ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
    API_VERSION: str = os.getenv("WHATSAPP_API_VERSION", "v19.0")

    # Database & Storage
    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", "data/recipients.db"))

    # Engine Settings
    RATE_LIMIT_DELAY_SECONDS: float = float(
        os.getenv("RATE_LIMIT_DELAY_SECONDS", "1.5")
    )
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> None:
        """Validates that necessary operational environment variables exist."""
        missing = []
        if not self.ACCESS_TOKEN:
            missing.append("WHATSAPP_ACCESS_TOKEN")
        if not self.PHONE_NUMBER_ID:
            missing.append("WHATSAPP_PHONE_NUMBER_ID")

        if missing:
            raise ValueError(
                f"Missing critical configuration variables: {', '.join(missing)}. "
                f"Please update your .env file."
            )


config = Config()