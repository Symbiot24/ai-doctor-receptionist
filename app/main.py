from app.telegram.bot import run_bot
from loguru import logger

from app.router.intent_router import IntentRouter

logger.info(IntentRouter.detect("Book appointment"))
logger.info(IntentRouter.detect("Cancel tomorrow booking"))
logger.info(IntentRouter.detect("Change my appointment"))
logger.info(IntentRouter.detect("Hello"))

if __name__ == "__main__":
    run_bot()