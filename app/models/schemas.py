from pydantic import BaseModel
from typing import Optional, List, Any


# ── Incoming Webhook Payload ────────────────────────────────────────────────

class TextMessage(BaseModel):
    body: str


class IncomingMessage(BaseModel):
    id: str
    from_: str  # sender phone number
    timestamp: str
    type: str
    text: Optional[TextMessage] = None

    model_config = {"populate_by_name": True}

    @classmethod
    def from_raw(cls, data: dict) -> "IncomingMessage":
        # 'from' is a Python keyword, so we rename it
        data = dict(data)
        data["from_"] = data.pop("from", "")
        return cls(**data)


class WebhookValue(BaseModel):
    messaging_product: str
    metadata: dict
    contacts: Optional[List[dict]] = None
    messages: Optional[List[dict]] = None
    statuses: Optional[List[dict]] = None


class WebhookChange(BaseModel):
    value: WebhookValue
    field: str


class WebhookEntry(BaseModel):
    id: str
    changes: List[WebhookChange]


class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[WebhookEntry]


# ── Outgoing Message ─────────────────────────────────────────────────────────

class OutgoingTextMessage(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "text"
    text: dict


# ── Chat Session (in-memory, no DB) ─────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatSession(BaseModel):
    phone: str
    messages: List[ChatMessage] = []

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(ChatMessage(role=role, content=content))
        # Keep only the last 6 messages (3 turns) to save TPM (Tokens Per Minute) limit
        if len(self.messages) > 6:
            self.messages = self.messages[-6:]

    def get_openai_history(self) -> list[dict]:
        """Return conversation history in OpenAI/Groq message format."""
        return [{"role": m.role, "content": m.content} for m in self.messages]


# ── Health Check ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
