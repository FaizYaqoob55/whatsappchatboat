"""
WhatsApp Cloud API Service
Meta API ko call karke messages bhejta hai
"""
import httpx
from loguru import logger
from app.core.config import get_settings


settings = get_settings()


async def send_text_message(to: str, message: str) -> bool:
    """
    Customer ko WhatsApp text message bhejo.
    Returns True if successful, False otherwise.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }

    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.whatsapp_api_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            logger.info(f"Message sent to {to} | status={response.status_code}")
            return True

    except httpx.HTTPStatusError as e:
        logger.error(
            f"WhatsApp API HTTP error | to={to} | "
            f"status={e.response.status_code} | body={e.response.text}"
        )
        return False

    except httpx.RequestError as e:
        logger.error(f"WhatsApp API request error | to={to} | error={e}")
        return False


async def send_typing_indicator(to: str) -> None:
    """
    'Typing...' indicator bhejo (optional, nice UX).
    """
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": to,  # best-effort
    }
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"https://graph.facebook.com/v19.0/{settings.whatsapp_phone_number_id}/messages",
                json=payload,
                headers=headers,
            )
    except Exception:
        pass  # typing indicator fail hona critical nahi
