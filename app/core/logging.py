import sys
from loguru import logger
from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()

    logger.remove()  # default handler remove karo

    # Console logger (human-readable)
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File logger (production ke liye)
    if settings.is_production:
        logger.add(
            "logs/app.log",
            level="INFO",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} — {message}",
        )

    logger.info(f"Logging initialized | env={settings.app_env} | level={settings.log_level}")
