"""
Chatbot Brain — Powered by Groq AI
=====================================
Single Groq API call with a rich system prompt.
The AI will:
  - Understand what the customer is asking (any language)
  - Handle greetings / order status / price / complaints — all via AI understanding
  - Reply in the same language the customer used
  - Load business details from business_data.json at repo root
  - No keyword matching — pure AI contextual understanding
"""
import json
from pathlib import Path

from loguru import logger
from groq import AsyncGroq

from app.core.config import get_settings
from app.models.schemas import ChatSession

settings = get_settings()

# ── In-Memory Chat Sessions (phone → ChatSession) ────────────────────────────
_sessions: dict[str, ChatSession] = {}


def _load_business_data() -> dict:
    """Load business details from business_data.json at repo root.
    Falls back to settings values if the file is missing or malformed.
    """
    data_path = Path(__file__).resolve().parents[2] / "business_data.json"
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Build a rich description from all available fields
        description_parts = [data.get("business_description", "")]
        if data.get("working_hours"):
            description_parts.append(f"Working hours: {data['working_hours']}")
        if data.get("contact_number"):
            description_parts.append(f"Contact: {data['contact_number']}")
        if data.get("delivery_time"):
            description_parts.append(f"Delivery time: {data['delivery_time']}")
        if data.get("payment_methods"):
            methods = ", ".join(data["payment_methods"])
            description_parts.append(f"Payment methods: {methods}")
        if data.get("return_policy"):
            description_parts.append(f"Return policy: {data['return_policy']}")
        if data.get("price_range"):
            description_parts.append(f"Price range: {data['price_range']}")

        return {
            "business_name": data.get("business_name", settings.business_name),
            "business_description": "\n".join(description_parts),
        }
    except Exception as e:
        logger.warning(f"Could not load business_data.json, using settings fallback | error={e}")
        return {
            "business_name": settings.business_name,
            "business_description": settings.business_description,
        }



def get_or_create_session(phone: str) -> ChatSession:
    if phone not in _sessions:
        _sessions[phone] = ChatSession(phone=phone)
        logger.debug(f"New session | phone={phone}")
    return _sessions[phone]


def clear_session(phone: str) -> None:
    _sessions.pop(phone, None)


# ── System Prompt ─────────────────────────────────────────────────────────────

def build_system_prompt() -> str:
    """Build the AI system prompt using business data loaded from JSON file."""
    biz = _load_business_data()
    return f"""
You are a smart and friendly WhatsApp customer service agent for "{biz['business_name']}".

Business information:
{biz['business_description']}

Your responsibilities:
1. Read and fully understand the customer's message — do NOT rely on keyword matching.
2. Provide a helpful, accurate, and natural-sounding reply based on the business information above.
3. Detect the language of the user's message (English, Roman Urdu, Urdu, or any other language) and reply in that exact same language.
4. Use WhatsApp formatting only: *bold*, _italic_, and line breaks. Keep replies to 4–5 lines max.
5. If the customer asks something outside the scope of the business, politely say so and offer to connect them to a human agent.

Guidelines for common intents:
- GREETINGS (hi, hello, salam, aoa, etc.): Warmly welcome the user, mention the business name, and offer to help. Use 1 emoji.
- ORDER STATUS (delivery, tracking, parcel, kab ayega, etc.): Ask for the order ID if not provided. Give a realistic timeline (e.g., 2–3 working days). Be sympathetic.
- PRICE INQUIRY (price, qeemat, rate, cost, kitna, etc.): Give price ranges or specific prices from the business data. Mention discounts or deals if applicable.
- COMPLAINTS (problem, issue, damage, refund, return, galat, etc.): Sincerely apologize, empathize, explain resolution steps, and offer to escalate to a human agent.
- HUMAN AGENT REQUEST (agent, manager, insaan, call, etc.): Acknowledge and share working hours (Monday–Saturday, 9 AM–6 PM) and contact number 0300-XXXXXXX.
- GENERAL QUESTIONS: Answer accurately using business context. If unsure, be honest and suggest a human agent.

IMPORTANT RULES:
- ALWAYS respond in the same language as the customer's message.
- NEVER switch languages unless the customer does.
- Keep replies short, warm, and human — avoid robotic or formal phrasing.
- Use 1–2 relevant emojis per reply (not more).
- If customer seems angry or frustrated, be extra empathetic and calm.
""".strip()


# ── Main Reply Generator ──────────────────────────────────────────────────────

async def generate_reply(phone: str, message: str) -> str:
    """Generate a natural AI reply for the customer's message using Groq.
    The AI understands intent from context — no manual keyword matching needed.
    """
    session = get_or_create_session(phone)
    session.add_message("user", message)

    logger.info(f"Generating AI reply | phone={phone} | msg='{message[:60]}'")

    reply = await _call_groq(session)

    session.add_message("assistant", reply)
    logger.info(f"Reply ready | phone={phone} | reply='{reply[:60]}'")
    return reply


async def _call_groq(session: ChatSession) -> str:
    """Call the Groq API with the system prompt and full conversation history."""
    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY not set in .env!")
        return "⚠️ The bot is not configured yet. Please try again later."

    try:
        client = AsyncGroq(api_key=settings.groq_api_key)

        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]
        # Include full conversation history so AI has context
        messages.extend(session.get_openai_history())

        response = await client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            max_tokens=400,
            temperature=0.7,
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
            "Sorry, we're experiencing a technical issue right now. 😔\n"
            "Please try again in a moment or call us at *0300-XXXXXXX*."
        )
