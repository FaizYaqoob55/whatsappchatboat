"""
Intent Detection Service — LEGACY / UNUSED
==========================================
Ye module currently chatbot.py mein use nahi hota.
Groq AI automatically intent samajhta hai system prompt ke zariye.

Agar future mein pre-processing ya routing logic chahiye ho
(e.g., specific intents ke liye alag handlers), tab ye module
use mein aayega. Abhi sirf reference ke liye rakha gaya hai.
"""
from enum import Enum
import re


class Intent(str, Enum):
    ORDER_STATUS   = "order_status"
    GREETING       = "greeting"
    FAREWELL       = "farewell"
    COMPLAINT      = "complaint"
    HUMAN_AGENT    = "human_agent"
    PRICE_INQUIRY  = "price_inquiry"
    GENERAL        = "general"


# ── Keyword Maps ─────────────────────────────────────────────────────────────

_ORDER_KEYWORDS = [
    "order", "orders", "oder",  # typo bhi
    "kab ayga", "kab aaye ga", "kab milega",
    "delivery", "deliver", "shipment", "ship",
    "tracking", "track", "parcel",
    "mera order", "meri delivery",
    "status", "update",
]

_GREETING_KEYWORDS = [
    "hi", "hello", "helo", "hey",
    "salam", "salaam", "assalam", "aoa",
    "good morning", "good evening", "good afternoon",
    "kya hal", "kaise ho", "kia hal",
    "start",
]

_FAREWELL_KEYWORDS = [
    "bye", "goodbye", "good bye",
    "khuda hafiz", "allah hafiz",
    "thanks", "thank you", "shukriya", "shukria",
    "ok done", "theek hai", "theek ha",
]

_COMPLAINT_KEYWORDS = [
    "complaint", "complain",
    "problem", "issue", "masla", "mushkil",
    "wrong", "galat", "broken", "damage", "damaged",
    "refund", "return", "wapas",
    "frustrated", "angry", "worst",
]

_HUMAN_KEYWORDS = [
    "agent", "human", "insaan", "banda",
    "real person", "customer service",
    "manager", "senior",
    "baat karni hai", "call karo",
]

_PRICE_KEYWORDS = [
    "price", "qeemat", "kitna", "cost",
    "rate", "charges", "fee",
    "how much", "kitne ka",
]


def detect_intent(message: str) -> Intent:
    """
    Message ka intent detect karo (keyword-based).
    Returns Intent enum value.

    NOTE: Ye function currently active code mein call nahi hota.
    Groq AI directly intent handle karta hai via system prompt.
    """
    text = message.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)  # punctuation remove

    if _matches(text, _HUMAN_KEYWORDS):
        return Intent.HUMAN_AGENT

    if _matches(text, _COMPLAINT_KEYWORDS):
        return Intent.COMPLAINT

    if _matches(text, _ORDER_KEYWORDS):
        return Intent.ORDER_STATUS

    if _matches(text, _PRICE_KEYWORDS):
        return Intent.PRICE_INQUIRY

    if _matches(text, _GREETING_KEYWORDS):
        return Intent.GREETING

    if _matches(text, _FAREWELL_KEYWORDS):
        return Intent.FAREWELL

    return Intent.GENERAL


def _matches(text: str, keywords: list[str]) -> bool:
    for kw in keywords:
        if kw in text:
            return True
    return False
