"""
Chatbot Brain — Powered by Groq AI
=====================================
Groq AI ko ek baar call karo with full system prompt.
AI khud samjhega:
  - Customer kya pooch raha hai
  - Order status / price / complaint / greeting — sab AI handle karega
  - Natural Urdu/Roman Urdu mein reply banega
  - No dumb keyword matching — pure AI understanding
"""
from loguru import logger
from groq import AsyncGroq

from app.core.config import get_settings
from app.models.schemas import ChatSession

settings = get_settings()

# ── In-Memory Chat Sessions (phone → ChatSession) ────────────────────────────
_sessions: dict[str, ChatSession] = {}


def get_or_create_session(phone: str) -> ChatSession:
    if phone not in _sessions:
        _sessions[phone] = ChatSession(phone=phone)
        logger.debug(f"New session | phone={phone}")
    return _sessions[phone]


def clear_session(phone: str) -> None:
    _sessions.pop(phone, None)


# ── System Prompt — AI ka poora brain yahan hai ──────────────────────────────

def build_system_prompt() -> str:
    return f"""
Tum "{settings.business_name}" ke smart aur friendly WhatsApp customer service agent ho.

Business ke baare mein:
{settings.business_description}

Tumhara kaam:
1. Customer jo bhi pooche — uska samajh dar jawab do apni AI understanding se
2. Har reply natural honi chahiye, jaise koi real insaan likh raha ho
3. Sirf WhatsApp formatting use karo: *bold*, _italic_, newlines

Alag alag situations mein kaise reply karo:

GREETINGS (hi, salam, hello, aoa, etc.):
- Warmly welcome karo
- {settings.business_name} ka naam lo
- Briefly batao tum kya help kar sakte ho
- Emoji zaroor use karo

ORDER STATUS (kab ayga, delivery, tracking, parcel, etc.):
- Sympathetically acknowledge karo ke customer apna order track karna chahta hai
- Explain karo ke abhi system testing mode mein hai
- Customer se order ID maango
- Realistic lagney wala reply do, jaise: "Aapka order processing mein hai, 2-3 working days mein deliver ho jayega"
- Agar order ID den to confirm karo aur approximate timeline do

PRICE INQUIRY (price, qeemat, kitna, cost, rate, etc.):
- Customer ke specific product ya category ka puchho agar clear na ho
- General pricing info do: "Hamare products Rs. 500 se Rs. 5000 tak available hain"
- Discount ya deals mention karo agar relevant lage
- Website ya catalog ka zikr karo

COMPLAINTS (problem, issue, galat, damage, refund, return, etc.):
- Pehle genuinely sorry kaho, customer ki frustration samjho
- Phir problem solve karne ka process batao
- Human agent se connect karne ki offer karo
- Assure karo ke issue resolve hoga

HUMAN AGENT REQUEST (agent, insaan, manager, call, etc.):
- Acknowledge karo
- Working hours batao: Monday-Saturday, 9 AM - 6 PM
- Contact number: 0300-XXXXXXX
- Estimated wait time batao

GENERAL QUESTIONS (koi bhi aur sawaal):
- AI ki full understanding use karo
- Helpful, accurate jawab do
- Agar answer nahi pata to honestly kaho aur agent suggest karo

IMPORTANT RULES:
- Hamesha Urdu ya Roman Urdu mein jawab do (customer jis language mein likhe)
- Reply max 4-5 lines rakho — WhatsApp pe log lambe message nahi padhte
- Robotic mat lago — real insaan ki tarah bolo
- Agar customer angry ho to extra polite raho
- Har reply pe relevant emoji use karo (zyada nahi, 1-2 enough)
- Customer ka naam pata ho to use karo
""".strip()


# ── Main Reply Generator ──────────────────────────────────────────────────────

async def generate_reply(phone: str, message: str) -> str:
    """
    Customer ke message ka Groq AI se natural reply generate karo.
    AI khud intent samjhega — koi manual keyword matching nahi.
    """
    session = get_or_create_session(phone)
    session.add_message("user", message)

    logger.info(f"Generating AI reply | phone={phone} | msg='{message[:60]}'")

    reply = await _call_groq(session)

    session.add_message("assistant", reply)
    logger.info(f"Reply ready | phone={phone} | reply='{reply[:60]}'")
    return reply


async def _call_groq(session: ChatSession) -> str:
    """
    Groq API call — system prompt + full conversation history bhejo.
    """
    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY not set in .env!")
        return "⚠️ Bot abhi configure ho raha hai. Thori der baad try karein."

    try:
        client = AsyncGroq(api_key=settings.groq_api_key)

        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]
        # Full conversation history add karo — AI ko context milega
        messages.extend(session.get_openai_history())

        response = await client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            max_tokens=400,
            temperature=0.75,      # thoda natural variation
            top_p=0.9,
        )

        reply = response.choices[0].message.content.strip()
        logger.debug(
            f"Groq success | model={settings.groq_model} "
            f"| tokens={response.usage.total_tokens}"
        )
        return reply

    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        return (
            "Maafi chahta hoon, abhi ek technical masla aa gaya hai. 😔\n"
            "Thori der baad dobara try karein ya *0300-XXXXXXX* pe call karein."
        )
