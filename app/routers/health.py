"""
Health Check Router
Server ka status check karne ke liye
"""
from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.core.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/", include_in_schema=False)
async def root() -> dict:
    return {"message": f"{settings.business_name} WhatsApp Chatbot is running! 🚀"}


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.app_env,
    )
