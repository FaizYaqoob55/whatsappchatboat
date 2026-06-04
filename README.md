# 📱 WhatsApp AI Chatbot — FastAPI

Production-ready WhatsApp chatbot with AI replies, intent detection, and order status handling.

---

## 📁 Folder Structure

```
whatsapp-chatbot/
├── app/
│   ├── main.py               ← FastAPI app entry point
│   ├── core/
│   │   ├── config.py         ← Settings & env variables
│   │   └── logging.py        ← Loguru setup
│   ├── routers/
│   │   ├── webhook.py        ← /webhook GET + POST
│   │   └── health.py         ← /health endpoint
│   ├── services/
│   │   ├── chatbot.py        ← Main brain — reply generate karo
│   │   ├── intent.py         ← Message ka intent detect karo
│   │   └── whatsapp.py       ← Meta API — message bhejo
│   ├── models/
│   │   └── schemas.py        ← Pydantic models
│   └── utils/
│       └── helpers.py        ← Utility functions
├── tests/
│   └── test_webhook.py       ← pytest tests
├── .env.example              ← Environment variables template
├── requirements.txt
├── Dockerfile
├── render.yaml               ← Render.com deploy config
└── README.md
```

---

## 🚀 Local Setup (Step 1)

```bash
# 1. Project folder mein jao
cd whatsapp-chatbot

# 2. Virtual environment banao
python -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows

# 3. Dependencies install karo
pip install -r requirements.txt

# 4. .env file banao
cp .env.example .env
```

`.env` file mein apni values daalo:

```env
WHATSAPP_TOKEN=EAAxxxxxxxxxx...
WHATSAPP_PHONE_NUMBER_ID=12345678901234
WHATSAPP_VERIFY_TOKEN=mera_secret_verify_token_123
OPENAI_API_KEY=sk-xxxxxxxxxxxx
BUSINESS_NAME=Mera Online Store
```

```bash
# 5. Server start karo
uvicorn app.main:app --reload --port 8000

# Server yahan available hoga:
# http://localhost:8000
# http://localhost:8000/docs  ← Swagger UI
# http://localhost:8000/health
```

---

## 🌐 Deploy to Render.com (Step 2)

1. GitHub pe repo push karo:
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   git remote add origin https://github.com/TUMHARA_USERNAME/whatsapp-chatbot.git
   git push -u origin main
   ```

2. **render.com** pe jao → "New" → "Web Service"
3. GitHub repo connect karo
4. Environment variables daalo (dashboard mein):
   - `WHATSAPP_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_VERIFY_TOKEN`
   - `OPENAI_API_KEY`
5. Deploy karo — tumhara URL milega: `https://whatsapp-chatbot-xxxx.onrender.com`

---

## 📲 Meta WhatsApp Setup (Step 3)

1. **developers.facebook.com** pe jao
2. "My Apps" → "Create App" → "Business" select karo
3. Left menu mein "WhatsApp" → "API Setup"
4. **Phone Number ID** copy karo
5. **Access Token** generate karo (temporary ya permanent)
6. **Webhook** section mein:
   - Callback URL: `https://whatsapp-chatbot-xxxx.onrender.com/webhook`
   - Verify Token: `mera_secret_verify_token_123` (jo .env mein daala)
   - "messages" field subscribe karo
7. "Verify and Save" click karo ✅

---

## 🧪 Test Karo (Step 4)

Meta dashboard mein "To" field mein apna personal WhatsApp number daalo aur test message bhejo.

Ya curl se test karo:
```bash
# Health check
curl https://whatsapp-chatbot-xxxx.onrender.com/health

# Manual webhook test
curl -X POST https://whatsapp-chatbot-xxxx.onrender.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "123",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "metadata": {"display_phone_number": "15550001111", "phone_number_id": "123"},
          "messages": [{
            "from": "923001234567",
            "id": "msg1",
            "timestamp": "1700000000",
            "type": "text",
            "text": {"body": "hi"}
          }]
        },
        "field": "messages"
      }]
    }]
  }'
```

---

## 🧪 Unit Tests

```bash
pytest tests/ -v
```

---

## 💬 Bot Kya Kya Kar Sakta Hai

| Customer Likhey | Bot Ka Jawab |
|---|---|
| "hi" / "salam" | Welcome message + menu |
| "mera order kab ayga?" | Order status reply |
| "price kya hai?" | Price inquiry reply |
| "complaint hai" | Complaint handler + agent offer |
| "agent se baat karni hai" | Human handoff message |
| Koi bhi aur sawaal | OpenAI GPT se AI reply |

---

## 🔧 Customize Karo

- **Business name/description**: `.env` mein `BUSINESS_NAME` change karo
- **Fixed replies**: `app/services/chatbot.py` mein strings edit karo
- **New intents**: `app/services/intent.py` mein keywords add karo
- **Database connect**: `chatbot.py` mein `handleOrderQuery` function update karo
