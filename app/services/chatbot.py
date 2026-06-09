"""
CareDesk — AI Sales & Support Agent
=====================================
Powered by Groq AI (llama-3.1-8b-instant)

This agent acts as a real human representative of CareDesk IT & Digital Agency.
It handles:
  - Service inquiries (web dev, app dev, AI chatbots, social media, design)
  - Portfolio / past work questions
  - Process & timeline questions
  - Pricing inquiries (redirects to email — no pricing on chat)
  - General business questions
  - Lead qualification & next steps

Behaviour:
  - Responds in the same language the customer uses (English / Roman Urdu / Urdu)
  - Sounds like a real human — warm, confident, professional
  - Never robotic, never shows menus, never uses bullet points in replies
  - Short, crisp WhatsApp-style messages (3-5 lines max)
"""

import json
from pathlib import Path

from loguru import logger
from groq import AsyncGroq

from app.core.config import get_settings
from app.models.schemas import ChatSession
from app.services.session_store import SessionStore

settings = get_settings()

# ── Persistent Session Store ──────────────────────────────────────────────────
_session_store = SessionStore()


# ── Business Data Loader ──────────────────────────────────────────────────────

def _load_business_data() -> dict:
    """Load full CareDesk business data from business_data.json."""
    data_path = Path(__file__).resolve().parents[2] / "business_data.json"
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load business_data.json: {e}")
        return {}


def _build_knowledge_base(data: dict) -> str:
    """Convert the business JSON into a rich, structured knowledge base string for the AI."""
    if not data:
        return "CareDesk — IT & Digital Agency. Email: info@caredesko.com"

    services = data.get("services", {})
    portfolio = data.get("portfolio_clients", [])
    faqs = data.get("faqs", {})
    process = data.get("process", [])
    why_us = data.get("why_choose_us", [])

    kb = f"""
COMPANY: {data.get('business_name', 'CareDesk')}
TAGLINE: {data.get('business_tagline', '')}
TYPE: {data.get('business_type', '')}
ABOUT: {data.get('business_description', '')}
WEBSITE: {data.get('website', 'https://www.caredesko.com')}
EMAIL: {data.get('email', 'info@caredesko.com')}
WORKING HOURS: {data.get('working_hours', 'Monday–Saturday, 10 AM–7 PM PKT')}
RESPONSE TIME: {data.get('response_time', '')}

--- SERVICES ---

1. WEBSITE & APP DEVELOPMENT
{services.get('web_and_app_development', {}).get('description', '')}
What we build: {', '.join(services.get('web_and_app_development', {}).get('highlights', []))}

2. AI CHATBOT & AI CALLING ASSISTANT
{services.get('ai_solutions', {}).get('description', '')}
What we build: {', '.join(services.get('ai_solutions', {}).get('highlights', []))}

3. SOCIAL MEDIA MARKETING & MANAGEMENT
{services.get('social_media', {}).get('description', '')}
What we do: {', '.join(services.get('social_media', {}).get('highlights', []))}

4. GRAPHIC DESIGN & UI/UX DESIGN
{services.get('design', {}).get('description', '')}
What we do: {', '.join(services.get('design', {}).get('highlights', []))}

--- PORTFOLIO (RECENT CLIENTS) ---
{chr(10).join([f"• {c['name']} ({c['industry']}) — {c['url']} — {c['description']}" for c in portfolio])}

--- OUR PROCESS ---
{chr(10).join([f"Step {i+1}: {step}" for i, step in enumerate(process)])}

--- WHY CHOOSE CAREDESK ---
{chr(10).join([f"• {point}" for point in why_us])}

--- FREQUENTLY ASKED QUESTIONS ---
How long does a website take? {faqs.get('how_long_does_a_website_take', '')}
Do you work with startups? {faqs.get('do_you_work_with_startups', '')}
Revision policy? {faqs.get('what_is_your_revision_policy', '')}
Do you provide maintenance? {faqs.get('do_you_provide_maintenance', '')}
Which countries? {faqs.get('which_countries_do_you_work_with', '')}

--- PRICING POLICY (CRITICAL) ---
{data.get('pricing_policy', 'Pricing is not shared on WhatsApp. Please email info@caredesko.com for a custom quote.')}
""".strip()

    return kb


# ── System Prompt Builder ─────────────────────────────────────────────────────

def build_system_prompt() -> str:
    """Build the full AI system prompt for the CareDesk human-like agent."""
    data = _load_business_data()
    knowledge_base = _build_knowledge_base(data)

    return f"""
You are "Ayan", a friendly and professional Sales & Support Representative at CareDesk — a Pakistan-based IT and Digital Agency.

You are chatting on WhatsApp on behalf of CareDesk. Your job is to:
- Help potential clients understand CareDesk's services
- Answer questions naturally and confidently
- Qualify leads and guide them to the next step (contacting via email or booking a call)
- Represent the brand professionally and warmly

=== YOUR KNOWLEDGE BASE ===
{knowledge_base}

=== LANGUAGE RULES — FOLLOW STRICTLY ===
- Detect the language of the customer's message FIRST.
- If message is in ENGLISH → reply in ENGLISH only.
- If message contains Roman Urdu (like "kya", "hai", "karo", "bata", "chahiye", "hona", "mujhe", "aap", "kab", "karna") → reply in ROMAN URDU only.
- If message is in Urdu script → reply in Urdu script.
- If ambiguous (just "hi", "hello", "ok", "yes") → default to ENGLISH.
- NEVER mix languages in a single reply.
- NEVER switch language unless the customer switches first.

=== PERSONALITY & TONE ===
- You are warm, confident, and helpful — like a real person, NOT a robot.
- You are knowledgeable about tech and digital marketing but explain things in simple, relatable terms.
- You never sound salesy or pushy. You genuinely help.
- Use a professional yet friendly tone. Like a smart colleague, not a call center script.

=== REPLY STYLE RULES ===
- Keep replies SHORT — maximum 4-5 lines. WhatsApp is not email.
- NEVER show bullet point lists or numbered menus in your reply. Write in natural sentences.
- Use a maximum of 1-2 emojis per message. Not more.
- Use *bold* only for very important things (like email address, service name).
- NEVER start with "Hi! I'm a bot" or mention you're an AI. You are Ayan from CareDesk.
- NEVER say "How can I assist you today?" as a standalone response. Always add context.

=== HOW TO HANDLE DIFFERENT SITUATIONS ===

GREETING (hi, hello, salam, assalam o alikum, etc.):
→ Warmly greet them, introduce yourself as Ayan from CareDesk, and ask what they're looking for.
→ Example: "Hey! 👋 I'm Ayan from CareDesk. Great to hear from you — what can I help you with today?"

SERVICE INQUIRY (website, app, chatbot, social media, design):
→ Explain the relevant service confidently in 2-3 lines using the knowledge base above.
→ Then ask a qualifying question: what type of business, what do they need, do they have a reference in mind.
→ Mention portfolio examples naturally if relevant.

PRICING INQUIRY (cost, price, rate, kitna, budget, quote):
→ NEVER share any price. ALWAYS redirect to email politely.
→ Say something like: "For pricing, every project is custom-scoped so we share a proper quote based on your requirements. Drop us a message at *info@caredesko.com* and we'll get back to you with a detailed proposal within 24 hours! 🙌"
→ If they ask again — be firm but polite. Still redirect to email.

PORTFOLIO / PAST WORK questions:
→ Mention specific client names and industries naturally (Al Bashar Store, Maarij Sports, Serenity Himalayan, etc.)
→ Provide the website URL so they can check it out themselves.
→ Keep it brief and confident.

TIMELINE / HOW LONG questions:
→ Use the FAQ data: standard sites 1-2 weeks, e-commerce 3-6 weeks, etc.
→ Mention that timeline depends on project scope and they'll get an exact timeline in the proposal.

PROCESS questions (how does it work, kya process hai):
→ Briefly explain the 6-step process in a natural conversational way (not as a list).

COMPLAINTS or ISSUES:
→ Apologize sincerely and empathize.
→ Ask them to email *info@caredesko.com* with their concern so the relevant team can assist immediately.

NOT INTERESTED / GOODBYE:
→ Thank them for reaching out, wish them well, leave the door open.
→ "No worries at all! If you ever need anything digital, we're always here. Have a great day! 😊"

OFF-TOPIC (unrelated to CareDesk services):
→ Politely let them know you handle CareDesk-related queries and redirect.

=== CRITICAL RULES — NEVER BREAK THESE ===
1. NEVER share any pricing, cost, or rate — not even ranges. Always redirect to *info@caredesko.com*.
2. NEVER claim services CareDesk doesn't offer.
3. NEVER make up portfolio projects. Only use the ones in the knowledge base.
4. NEVER say you are an AI, a chatbot, or a bot. You are Ayan — a real team member.
5. NEVER show numbered or bulleted menus/options in your reply.
6. ALWAYS reply in the same language the customer used.
7. Keep every reply under 5 lines — no long paragraphs on WhatsApp.
""".strip()


# ── Session Helpers ───────────────────────────────────────────────────────────

def get_or_create_session(phone: str) -> ChatSession:
    """Retrieve existing session or create a fresh one for this phone number."""
    return _session_store.get_or_create(phone)


def clear_session(phone: str) -> None:
    """Clear the chat session for a given phone number."""
    _session_store.clear(phone)


# ── Main Reply Generator ──────────────────────────────────────────────────────

async def generate_reply(phone: str, message: str) -> str:
    """
    Generate a human-like AI reply for the customer's WhatsApp message.
    Uses full conversation context so the AI remembers what was discussed.
    Persists both user message and AI reply to disk after each exchange.
    """
    session = get_or_create_session(phone)
    session.add_message("user", message)

    logger.info(f"Generating reply | phone={phone} | msg='{message[:80]}'")

    reply = await _call_groq(session)

    session.add_message("assistant", reply)
    # ✅ Persist conversation to disk so no messages are lost on restart
    _session_store.save(phone)
    logger.info(f"Reply sent | phone={phone} | preview='{reply[:80]}'")
    return reply


async def _call_groq(session: ChatSession) -> str:
    """Call the Groq API with the full conversation history and system prompt."""
    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY not configured in .env!")
        return (
            "Hey! Our chat system is being set up. Please reach out directly at "
            "*info@caredesko.com* and we'll get back to you shortly! 🙌"
        )

    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)

        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]
        messages.extend(session.get_openai_history())

        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            max_tokens=450,
            temperature=0.75,
            top_p=0.95,
        )

        reply = response.choices[0].message.content.strip()
        logger.debug(
            f"Groq response | model={settings.GROQ_MODEL} "
            f"| tokens={response.usage.total_tokens}"
        )
        return reply

    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        return (
            "Sorry for the inconvenience! 😔 Please drop us an email at "
            "*info@caredesko.com* and our team will get back to you right away."
        )
