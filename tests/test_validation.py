"""
Unit tests for phone number validation, E.164 conversion, and input rules.
"""

import pytest
from validation import ValidationError, validate_message_text, validate_phone_number, validate_positive_integer


def test_valid_international_phone():
    # Valid Indian format
    assert validate_phone_number("+919876543210") == "+919876543210"
    # Auto-appends '+' if missing
    assert validate_phone_number("919876543210") == "+919876543210"
    # US format
    assert validate_phone_number("+14155552671") == "+14155552671"


def test_invalid_phone_numbers():
    with pytest.raises(ValidationError):
        validate_phone_number("")

    with pytest.raises(ValidationError):
        validate_phone_number("invalid_phone_str")

    with pytest.raises(ValidationError):
        validate_phone_number("+123")  # Too short


def test_positive_integer_validation():
    assert validate_positive_integer("5") == 5
    assert validate_positive_integer("  10  ") == 10

    with pytest.raises(ValidationError):
        validate_positive_integer("0")

    with pytest.raises(ValidationError):
        validate_positive_integer("-3")

    with pytest.raises(ValidationError):
        validate_positive_integer("abc")


def test_message_text_validation():
    assert validate_message_text("Hello World") == "Hello World"

    with pytest.raises(ValidationError):
        validate_message_text("   ")