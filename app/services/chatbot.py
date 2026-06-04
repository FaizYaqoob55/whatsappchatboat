"""
Chatbot Brain Service
Intent ke mutabiq sahi reply generate karta hai.
In-memory chat sessions (no DB needed for testing).
"""
from loguru import logger
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.models.schemas import ChatSession
from app.services.intent import detect_intent, Intent

settings = get_settings()

# ── In-Memory Session Store (phone → ChatSession) ────────────────────────────
# Production mein Redis se replace kar dena, abhi testing ke liye yahi kaafi hai
_sessions: dict[str, ChatSession] = {}


def get_or_create_session(phone: str) -> ChatSession:
    if phone not in _sessions:
        _sessions[phone] = ChatSession(phone=phone)
        logger.debug(f"New session created | phone={phone}")
    return _sessions[phone]


def clear_session(phone: str) -> None:
    _sessions.pop(phone, None)
    logger.debug(f"Session cleared | phone={phone}")


# ── Fixed Replies ─────────────────────────────────────────────────────────────

_GREETING_REPLY = """\
👋 *Assalam o Alaikum!* {business_name} mein khush aamdeed!

Main aapki kaise madad kar sakta hoon? 😊

Aap ye puch sakte hain:
• 📦 *Order status* — "mera order kab ayga?"
• 💰 *Prices* — "price kya hai?"
• 🙋 *Human agent* — "mujhe agent se baat karni hai"
• Koi bhi aur sawaal!"""

_ORDER_STATUS_REPLY = """\
📦 *Order Status*

Abhi hum database se connect nahi hain (testing mode). 

Agar aap order number bhejein to main check kar sakta hoon! 

*Example:* ORD-12345

_(Jald hi real-time order tracking available hogi!)_"""

_FAREWELL_REPLY = """\
🙏 *Shukriya* {business_name} se contact karne ka!

Kisi bhi waqt dobara message kar saktay hain. Allah Hafiz! 😊"""

_COMPLAINT_REPLY = """\
😔 Mujhe afsos hai ke aapko koi takleef hui.

Aapki complaint hamein zaroor solve karni chahiye.

🔴 *Kya aap chahte hain ke main aapko ek human agent se connect karoon?*

Bas "haan" ya "agent" likh kar bhejein."""

_HUMAN_AGENT_REPLY = """\
👨‍💼 *Human Agent se Connection*

Main abhi aapko hamari team ko forward kar raha hoon.

⏳ *Expected wait time:* 5-10 minutes

Hamare working hours hain:
🕘 *Monday-Saturday:* 9 AM – 6 PM

Agar urgent ho to aap is number pe call bhi kar saktay hain:
📞 *0300-XXXXXXX*"""

_PRICE_REPLY = """\
💰 *Price Inquiry*

Hamari website pe updated prices available hain.

Kisi specific product ka price chahiye to product ka naam bhejein, main help karoonga! 🛍️"""

_FALLBACK_REPLY = """\
Maafi chahta hoon, main samajh nahi paya. 

Kya aap dobara likh sakte hain? Ya main aapko *human agent* se connect kar doon?"""


# ── Main Reply Generator ──────────────────────────────────────────────────────

async def generate_reply(phone: str, message: str) -> str:
    """
    Customer ke message ka intent detect karo aur reply do.
    """
    session = get_or_create_session(phone)
    session.add_message("user", message)

    intent = detect_intent(message)
    logger.info(f"Intent detected | phone={phone} | intent={intent} | msg='{message[:50]}'")

    biz = settings.business_name

    if intent == Intent.GREETING:
        reply = _GREETING_REPLY.format(business_name=biz)

    elif intent == Intent.ORDER_STATUS:
        reply = _ORDER_STATUS_REPLY

    elif intent == Intent.FAREWELL:
        reply = _FAREWELL_REPLY.format(business_name=biz)

    elif intent == Intent.COMPLAINT:
        reply = _COMPLAINT_REPLY

    elif intent == Intent.HUMAN_AGENT:
        reply = _HUMAN_AGENT_REPLY
        clear_session(phone)  # Session reset after handoff

    elif intent == Intent.PRICE_INQUIRY:
        reply = _PRICE_REPLY

    else:
        # General question — AI se reply lo
        reply = await _get_ai_reply(session, message)

    session.add_message("assistant", reply)
    return reply


async def _get_ai_reply(session: ChatSession, user_message: str) -> str:
    """
    OpenAI GPT se context-aware reply generate karo.
    """
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set — using fallback reply")
        return _FALLBACK_REPLY

    system_prompt = f"""\
Tum {settings.business_name} ke helpful customer service assistant ho.

Business description: {settings.business_description}

Rules:
1. Hamesha Urdu ya Roman Urdu mein jawab do (customer jis language mein likhe)
2. Jawab concise rakho (3-5 lines max)
3. Friendly aur professional raho
4. Agar kuch nahi pata to honestly bol do aur agent se connect karne ki offer karo
5. Markdown bold (*text*) use kar sakte ho WhatsApp ke liye
6. Emojis use karo lekin zyada nahi"""

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(session.get_openai_history())

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
        logger.debug(f"AI reply generated | tokens={response.usage.total_tokens}")
        return reply

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return _FALLBACK_REPLY
