"""
Webhook Router
Meta WhatsApp se aane wale requests handle karta hai.

GET  /webhook  — Meta ka verification challenge
POST /webhook  — Incoming messages
"""
from fastapi import APIRouter, Request, Response, HTTPException, Query
from loguru import logger

from app.core.config import get_settings
from app.models.schemas import WhatsAppWebhookPayload, IncomingMessage
from app.services.chatbot import generate_reply
from app.services.whatsapp import send_text_message

router = APIRouter(prefix="/webhook", tags=["webhook"])
settings = get_settings()


# ── GET /webhook — Meta Verification ─────────────────────────────────────────

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> Response:
    """
    Meta pehli dafa webhook URL verify karne ke liye yahan GET request bhejta hai.
    Agar verify_token match kare to challenge wapas bhejo — tab Meta webhook accept karta hai.
    """
    logger.info(f"Webhook verification attempt | mode={hub_mode}")

    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.success("Webhook verified successfully!")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning("Webhook verification FAILED — token mismatch")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


# ── POST /webhook — Incoming Messages ────────────────────────────────────────

@router.post("")
async def receive_message(request: Request) -> dict:
    """
    Customer ka message yahan aata hai.
    Parse karo → reply generate karo → reply bhejo.
    Always return 200 to Meta (warna retry karta hai).
    """
    try:
        body = await request.json()
        logger.debug(f"Webhook payload received: {body}")

        payload = WhatsAppWebhookPayload(**body)

        # Saare entries aur changes process karo
        for entry in payload.entry:
            for change in entry.changes:
                value = change.value

                # Sirf 'messages' field process karo (status updates ignore)
                if not value.messages:
                    continue

                for raw_msg in value.messages:
                    try:
                        await _process_single_message(raw_msg)
                    except Exception as e:
                        # Log per-message errors so one bad message doesn't break others
                        logger.exception(f"Failed processing single message: {e}")

    except Exception as e:
        # Meta ko hamesha 200 chahiye, warna wo retry karta raha
        logger.error(f"Error processing webhook: {e}", exc_info=True)

    return {"status": "ok"}


async def _process_single_message(raw_msg: dict) -> None:
    """
    Ek message process karo — parse, reply generate, send.
    """
    # Sirf text messages handle karo (images/audio future mein)
    if raw_msg.get("type") != "text":
        logger.info(f"Non-text message ignored | type={raw_msg.get('type')}")
        return

    msg = IncomingMessage.from_raw(raw_msg)
    phone = msg.from_
    text = msg.text.body if msg.text else ""

    if not text.strip():
        return

    logger.info(f"Incoming message | from={phone} | text='{text[:80]}'")

    # Reply generate karo
    reply = await generate_reply(phone=phone, message=text)

    # Reply bhejo
    success = await send_text_message(to=phone, message=reply)

    if success:
        logger.success(f"Reply sent | to={phone} | reply='{reply[:60]}...'")
    else:
        logger.error(f"Failed to send reply | to={phone}")
