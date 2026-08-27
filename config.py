"""
Configuration manager loading environment variables safely for Twilio WhatsApp integration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Force load .env from the project root directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    @property
    def TWILIO_ACCOUNT_SID(self) -> str:
        return os.getenv("TWILIO_ACCOUNT_SID", "").strip("'\" ")

    @property
    def TWILIO_AUTH_TOKEN(self) -> str:
        return os.getenv("TWILIO_AUTH_TOKEN", "").strip("'\" ")

    @property
    def TWILIO_WHATSAPP_NUMBER(self) -> str:
        return os.getenv("TWILIO_WHATSAPP_NUMBER", "+17372212163").strip("'\" ")

    @property
    def DATABASE_PATH(self) -> Path:
        return Path(os.getenv("DATABASE_PATH", "data/recipients.db"))

    @property
    def RATE_LIMIT_DELAY_SECONDS(self) -> float:
        return float(os.getenv("RATE_LIMIT_DELAY_SECONDS", "1.5"))

    @property
    def MAX_RETRIES(self) -> int:
        return int(os.getenv("MAX_RETRIES", "3"))

    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> list[str]:
        """Validates that necessary operational environment variables exist."""
        missing = []
        if not self.TWILIO_ACCOUNT_SID:
            missing.append("TWILIO_ACCOUNT_SID")
        if not self.TWILIO_AUTH_TOKEN:
            missing.append("TWILIO_AUTH_TOKEN")
        return missing


config = Config()