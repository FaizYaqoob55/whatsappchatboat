"""
WhatsApp Chatbot — FastAPI Application
Main entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.routers import webhook, health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    setup_logging()
    from loguru import logger
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.business_name} WhatsApp Chatbot starting...")
    logger.info(f"   Environment : {settings.app_env}")
    logger.info(f"   Phone ID    : {settings.whatsapp_phone_number_id or 'NOT SET'}")
    logger.info(f"   Groq AI     : {'✅ configured' if settings.GROQ_API_KEY else '❌ NOT SET'}")
    logger.info("=" * 50)
    yield
    # ── Shutdown ──
    logger.info("Chatbot shutting down...")


app = FastAPI(
    title="WhatsApp Chatbot",
    description="AI-powered WhatsApp customer service bot",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

# CORS (webhook calls ke liye zaroor nahi but good practice)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(health.router)
app.include_router(webhook.router)
