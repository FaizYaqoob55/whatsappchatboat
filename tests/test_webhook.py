"""
Webhook Tests
pytest se run karo: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.core.config import get_settings

client = TestClient(app)
settings = get_settings()


# ── Webhook Verification Tests ────────────────────────────────────────────────

def test_webhook_verify_success():
    """Sahi token se verification kaam kare."""
    resp = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.whatsapp_verify_token,
            "hub.challenge": "test_challenge_abc123",
        },
    )
    assert resp.status_code == 200
    assert resp.text == "test_challenge_abc123"


def test_webhook_verify_wrong_token():
    """Galat token se 403 aaye."""
    resp = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "WRONG_TOKEN",
            "hub.challenge": "abc",
        },
    )
    assert resp.status_code == 403


# ── Incoming Message Tests ────────────────────────────────────────────────────

SAMPLE_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "ENTRY_ID",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"display_phone_number": "15550001111", "phone_number_id": "PHONE_ID"},
                "contacts": [{"profile": {"name": "Test User"}, "wa_id": "923001234567"}],
                "messages": [{
                    "from": "923001234567",
                    "id": "MSG_ID_001",
                    "timestamp": "1700000000",
                    "type": "text",
                    "text": {"body": "hi"}
                }]
            },
            "field": "messages"
        }]
    }]
}


@patch("app.routers.webhook.send_text_message", new_callable=AsyncMock, return_value=True)
@patch("app.routers.webhook.generate_reply", new_callable=AsyncMock, return_value="Test reply")
def test_incoming_message_returns_200(mock_reply, mock_send):
    """Incoming message pe hamesha 200 aana chahiye."""
    resp = client.post("/webhook", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("app.routers.webhook.send_text_message", new_callable=AsyncMock, return_value=True)
@patch("app.routers.webhook.generate_reply", new_callable=AsyncMock, return_value="Reply")
def test_generate_reply_called(mock_reply, mock_send):
    """generate_reply sahi phone aur message ke sath call ho."""
    client.post("/webhook", json=SAMPLE_PAYLOAD)
    mock_reply.assert_called_once_with(phone="923001234567", message="hi")


# ── Intent Tests ─────────────────────────────────────────────────────────────

from app.services.intent import detect_intent, Intent

def test_intent_greeting():
    assert detect_intent("hi") == Intent.GREETING
    assert detect_intent("Salam bhai") == Intent.GREETING

def test_intent_order():
    assert detect_intent("mera order kab ayga?") == Intent.ORDER_STATUS
    assert detect_intent("delivery kab hogi") == Intent.ORDER_STATUS

def test_intent_human():
    assert detect_intent("mujhe agent se baat karni hai") == Intent.HUMAN_AGENT

def test_intent_complaint():
    assert detect_intent("mera order galat aaya") == Intent.COMPLAINT

def test_intent_general():
    assert detect_intent("aaj mosam kaisa hai") == Intent.GENERAL


# ── Health Check ─────────────────────────────────────────────────────────────

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
