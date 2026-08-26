"""
Input validation utilities including phone number verification via E.164 standardization.
"""

import phonenumbers
from phonenumbers import NumberParseException


class ValidationError(Exception):
    """Custom exception raised when input data fails verification."""
    pass


def validate_phone_number(phone_str: str, default_region: str = "IN") -> str:
    """
    Validates and formats a raw phone string into E.164 standard (+919876543210).
    Raises ValidationError if invalid.
    """
    if not phone_str or not phone_str.strip():
        raise ValidationError("Phone number cannot be empty.")

    cleaned_input = phone_str.strip()
    
    # Auto-prepend '+' if omitted but starts with country code, default parsing:
    if not cleaned_input.startswith("+"):
        cleaned_input = f"+{cleaned_input}"

    try:
        parsed_number = phonenumbers.parse(cleaned_input, default_region)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError(f"'{phone_str}' is not a valid international phone number.")
        
        # Return strict E.164 formatted string
        return phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.E164
        )
    except NumberParseException as e:
        raise ValidationError(f"Invalid phone number format: {str(e)}")


def validate_positive_integer(value: str) -> int:
    """Validates that user input is a positive integer."""
    try:
        val = int(value.strip())
        if val <= 0:
            raise ValidationError("The count must be greater than zero.")
        return val
    except ValueError:
        raise ValidationError("Please enter a valid numeric integer.")


def validate_message_text(text: str) -> str:
    """Validates that a message body is not empty."""
    cleaned = text.strip()
    if not cleaned:
        raise ValidationError("Message text cannot be empty.")
    return cleaned