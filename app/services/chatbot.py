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
from app.services.session_store import SessionStore

settings = get_settings()

# ── Persistent Session Store (phone → ChatSession) ────────────────────────────
_session_store = SessionStore()


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
    """Retrieve an existing ChatSession for *phone* or create a new one.
    The SessionStore persists sessions to a JSON file, ensuring data survives process restarts.
    """
    return _session_store.get_or_create(phone)


def clear_session(phone: str) -> None:
    """Remove a chat session for *phone* from persistent storage."""
    _session_store.clear(phone)


# ── System Prompt ─────────────────────────────────────────────────────────────

def build_system_prompt() -> str:
    """Build the AI system prompt using business data loaded from JSON file."""
    biz = _load_business_data()
    return f"""
You are a smart, friendly, and professional WhatsApp customer service agent for "{biz['business_name']}".

=== BUSINESS INFORMATION ===
{biz['business_description']}

=== LANGUAGE RULE (CRITICAL — FOLLOW STRICTLY) ===
- Detect the language of the customer's message.
- If the message is in ENGLISH → reply in ENGLISH only.
- If the message contains Roman Urdu words (like "kya", "hai", "kab", "karo", "mujhe", "aap", etc.) → reply in ROMAN URDU only.
- If the message is in Urdu script → reply in Urdu script.
- If ambiguous (e.g. just "hi", "hello", "ok") → default to ENGLISH.
- NEVER mix languages. NEVER switch languages unless the customer does first.

=== RESPONSE STYLE RULES ===
- Sound like a real human, NOT a bot. Be warm and conversational.
- Keep replies to 3-4 lines MAX. WhatsApp users don't read long messages.
- NEVER show a menu or list of options in your greeting. Just welcome them naturally and ask how you can help.
- NEVER say things like "Aap ye puch sakte hain:" or show bullet point options. That is robotic.
- Use a maximum of 2 emojis per reply.
- Use WhatsApp formatting sparingly: *bold* for important words only.

=== HOW TO HANDLE INTENTS ===
- GREETING (hi, hello, salam, etc.): Give a warm 2-line welcome. Mention the business name. Ask how you can help. Do NOT list options.
- ORDER STATUS: Ask for order ID if not given. Provide a realistic timeline (2-3 working days).
- PRICE INQUIRY: Answer with specific prices or ranges from the business info above.
- COMPLAINT: Apologize sincerely, empathize, explain next steps, offer to connect to human agent.
- HUMAN AGENT: Share working hours and contact number from business info.
- ANYTHING ELSE: Use the business information above to answer. If unsure, honestly say so and offer human support.

=== CRITICAL RULES ===
- You MUST read and understand what the customer is actually asking. Do NOT rely on keywords.
- Your answer MUST come from the business information provided above.
- NEVER make up information not present in the business details.
- NEVER show a structured menu or list of options in any response.
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
    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY not set in .env!")
        return "⚠️ The bot is not configured yet. Please try again later."

    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)

        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]
        # Include full conversation history so AI has context
        messages.extend(session.get_openai_history())

        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            max_tokens=400,
            temperature=0.7,
            top_p=0.9,
        )

        reply = response.choices[0].message.content.strip()
        logger.debug(
            f"Groq success | model={settings.GROQ_MODEL} "
            f"| tokens={response.usage.total_tokens}"
        )
        return reply

    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        return (
            "Sorry, we're experiencing a technical issue right now. 😔\n"
            "Please try again in a moment or call us at *0300-XXXXXXX*."
        )
