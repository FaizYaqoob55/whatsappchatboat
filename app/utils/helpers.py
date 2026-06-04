"""
Utility helpers
"""
import re


def clean_phone_number(phone: str) -> str:
    """
    Phone number clean karo — sirf digits rakhna.
    Example: +92-300-1234567 → 923001234567
    """
    return re.sub(r"\D", "", phone)


def truncate_text(text: str, max_len: int = 100) -> str:
    """Logging ke liye text truncate karo."""
    return text[:max_len] + "..." if len(text) > max_len else text


def is_valid_whatsapp_number(phone: str) -> bool:
    """
    Basic WhatsApp number validation.
    Should be 10-15 digits (international format without +).
    """
    cleaned = clean_phone_number(phone)
    return 10 <= len(cleaned) <= 15
