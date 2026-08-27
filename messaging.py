"""
Messaging engine abstraction, Twilio WhatsApp integration,
rate limiting, retry mechanics, and message history logging.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from config import config
from database import db
from models import DeliveryStatus, MessageLog, Recipient
from recipients import MessageRepository

# Configure module logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=config.LOG_LEVEL)


class MessagingError(Exception):
    """Custom exception raised for unrecoverable messaging errors."""

    pass


# ============================================================================
# Provider Abstraction Interface
# ============================================================================


class BaseMessagingProvider(ABC):
    """
    Abstract Base Class for WhatsApp Messaging Providers.
    Swap providers (e.g., Meta, Twilio, Infobip) by implementing this interface.
    """

    @abstractmethod
    def send_text_message(
        self, recipient_phone: str, message_text: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Sends a custom text message to a single recipient phone number.

        :param recipient_phone: E.164 formatted phone number (+919876543210)
        :param message_text: Text body to be delivered
        :return: Tuple of (success_boolean, provider_message_id, error_message)
        """
        pass


# ============================================================================
# Twilio WhatsApp Implementation
# ============================================================================


import json

class TwilioWhatsAppProvider(BaseMessagingProvider):
    """
    Official Twilio WhatsApp Provider Client.
    """

    def __init__(self):
        config.validate()
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.from_number = config.TWILIO_WHATSAPP_NUMBER
        self.client = Client(self.account_sid, self.auth_token)

    def send_text_message(
        self, recipient_phone: str, message_text: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Dispatches a WhatsApp message using your account's Sandbox Content Template SID.
        """
        formatted_from = f"whatsapp:{self.from_number}"
        formatted_to = f"whatsapp:{recipient_phone if recipient_phone.startswith('+') else '+' + recipient_phone}"

        # PASTE THE HX... SID COPIED FROM THE API TAB HERE:
        my_account_template_sid = "HXb5b62575e6e4ff6129ad7c8efe1f983e"

        try:
            # Send via your active Sandbox Content Template
            message = self.client.messages.create(
                from_=formatted_from,
                to=formatted_to,
                content_sid="HXac51c61af94371da7904a767b414c2fc",
                content_variables=json.dumps({"1": message_text})
            )
            return True, message.sid, None

        except TwilioRestException as exc:
            error_desc = f"Twilio API Error [{exc.code}]: {exc.msg}"
            logger.error(f"Failed sending to {recipient_phone}: {error_desc}")
            return False, None, error_desc
        except Exception as exc:
            error_desc = f"Unexpected Error: {str(exc)}"
            logger.error(f"Failed sending to {recipient_phone}: {error_desc}")
            return False, None, error_desc

# ============================================================================
# Rate Limiting Engine
# ============================================================================


class RateLimiter:
    """Controls the dispatch rate between consecutive message attempts."""

    def __init__(self, delay_seconds: float = config.RATE_LIMIT_DELAY_SECONDS):
        self.delay_seconds = delay_seconds
        self.last_send_time = 0.0

    def wait(self) -> None:
        """Throttles request execution to conform to rate limit settings."""
        elapsed = time.time() - self.last_send_time
        if elapsed < self.delay_seconds:
            sleep_duration = self.delay_seconds - elapsed
            time.sleep(sleep_duration)
        self.last_send_time = time.time()


# ============================================================================
# Message History Audit Logging
# ============================================================================


class MessageLogRepository:
    """Manages persistent audit records for sent and failed messages."""

    def log_message(
        self,
        recipient_id: int,
        message_text: str,
        status: DeliveryStatus,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> MessageLog:
        """Persists a new delivery record to SQLite."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO message_logs 
                (recipient_id, message_text, status, provider_message_id, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    recipient_id,
                    message_text,
                    status.value,
                    provider_message_id,
                    error_message,
                ),
            )
            log_id = cursor.lastrowid
            return MessageLog(
                id=log_id,
                recipient_id=recipient_id,
                message_text=message_text,
                status=status,
                provider_message_id=provider_message_id,
                error_message=error_message,
            )

    def get_all_logs(self) -> List[Dict]:
        """Retrieves history joined with recipient names."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    ml.id, ml.recipient_id, r.name, r.phone_number,
                    ml.message_text, ml.status, ml.provider_message_id,
                    ml.error_message, ml.sent_at
                FROM message_logs ml
                JOIN recipients r ON ml.recipient_id = r.id
                ORDER BY ml.sent_at DESC
                """
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


# ============================================================================
# Messaging Orchestrator (Sending Engine)
# ============================================================================


class MessagingEngine:
    """
    Coordinates provider delivery, rate-limiting delays, automatic retries,
    and history logging.
    """

    def __init__(
        self,
        provider: Optional[BaseMessagingProvider] = None,
        rate_limiter: Optional[RateLimiter] = None,
        max_retries: int = config.MAX_RETRIES,
    ):
        self.provider = provider or TwilioWhatsAppProvider()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.log_repo = MessageLogRepository()
        self.max_retries = max_retries

    def send_single(self, recipient: Recipient, raw_message: str) -> MessageLog:
        """
        Sends a single personalized message with retry mechanics and rate limiting.
        """
        final_message = MessageRepository.render_personalized_message(
            raw_message, recipient
        )

        success = False
        provider_msg_id = None
        error_msg = None

        for attempt in range(1, self.max_retries + 1):
            self.rate_limiter.wait()

            logger.info(
                f"Sending message to {recipient.name} ({recipient.phone_number}) "
                f"[Attempt {attempt}/{self.max_retries}]..."
            )

            success, provider_msg_id, error_msg = (
                self.provider.send_text_message(
                    recipient.phone_number, final_message
                )
            )

            if success:
                logger.info(f"Successfully sent message to {recipient.name}")
                break

            if attempt < self.max_retries:
                backoff_time = attempt * 2.0
                logger.warning(
                    f"Attempt {attempt} failed for {recipient.name}. Retrying in {backoff_time}s..."
                )
                time.sleep(backoff_time)

        status = DeliveryStatus.SENT if success else DeliveryStatus.FAILED

        return self.log_repo.log_message(
            recipient_id=recipient.id,
            message_text=final_message,
            status=status,
            provider_message_id=provider_msg_id,
            error_message=error_msg,
        )

    def batch_send(
        self, items: List[Tuple[Recipient, str]]
    ) -> List[Tuple[Recipient, MessageLog]]:
        """
        Dispatches customized messages sequentially to a batch of recipients.
        """
        results = []
        for recipient, message_text in items:
            if not message_text or not message_text.strip():
                log_entry = self.log_repo.log_message(
                    recipient_id=recipient.id,
                    message_text="",
                    status=DeliveryStatus.SKIPPED,
                    error_message="Skipped: No custom message configured for recipient.",
                )
                results.append((recipient, log_entry))
                continue

            log_entry = self.send_single(recipient, message_text)
            results.append((recipient, log_entry))

        return results