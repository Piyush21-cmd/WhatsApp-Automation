"""
Unit tests for the messaging engine, rate limiting, and Meta API mocking.
"""

from unittest.mock import MagicMock, patch
import pytest
from models import DeliveryStatus, Recipient
from messaging import MetaWhatsAppProvider, MessagingEngine, RateLimiter


@pytest.fixture
def mock_recipient():
    return Recipient(id=1, name="Neha", phone_number="+919876543212")


def test_meta_provider_success_mock(mock_recipient):
    with patch("messaging.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "wamid.HBgLMTIzNDU2Nzg5MzA="}]
        }
        mock_post.return_value = mock_response

        # Mock configuration validation
        with patch("messaging.config.validate"):
            provider = MetaWhatsAppProvider()
            success, msg_id, error = provider.send_text_message(
                mock_recipient.phone_number, "Hello Neha"
            )

            assert success is True
            assert msg_id == "wamid.HBgLMTIzNDU2Nzg5MzA="
            assert error is None


def test_messaging_engine_retry_mechanics(mock_recipient, monkeypatch):
    mock_provider = MagicMock()
    # First attempt fails, second attempt succeeds
    mock_provider.send_text_message.side_effect = [
        (False, None, "Meta API Error 500: Internal Server Error"),
        (True, "wamid.12345", None),
    ]

    mock_rate_limiter = MagicMock(spec=RateLimiter)
    mock_log_repo = MagicMock()

    engine = MessagingEngine(
        provider=mock_provider,
        rate_limiter=mock_rate_limiter,
        max_retries=2,
    )
    engine.log_repo = mock_log_repo

    # Disable sleep delay during tests
    monkeypatch.setattr("messaging.time.sleep", lambda secs: None)

    log_result = engine.send_single(mock_recipient, "Hi {name}")

    assert mock_provider.send_text_message.call_count == 2
    mock_log_repo.log_message.assert_called_once()