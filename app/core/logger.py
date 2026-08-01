from loguru import logger

logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="10 days",
    level="INFO",
)

__all__ = ["logger"]