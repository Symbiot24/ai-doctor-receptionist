from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from app.core.config import TELEGRAM_BOT_TOKEN
from app.agent.ai_service import generate_reply

from app.router.intent_router import IntentRouter, Intent
from app.flows.booking.flow import BookingFlow
from app.state.state_manager import state_manager
from app.state.booking_state import BookingState

booking_flow = BookingFlow()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏥 Welcome to AI Doctor Appointment System!\n\n"
        "Type 'book appointment' to book an appointment."
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    telegram_message = update.effective_message

    if telegram_message is None or telegram_message.text is None:
        return

    user_id = update.effective_user.id
    message = telegram_message.text.strip()

    session = state_manager.get(user_id)

    try:
        # Continue booking if already in progress
        if session["state"] != BookingState.IDLE:

            reply = booking_flow.handle(
                user_id,
                message,
            )

        else:

            intent = IntentRouter.detect(message)

            if intent == Intent.BOOK:

                reply = booking_flow.start(user_id)

            else:

                reply = generate_reply(
                    user_id,
                    message,
                )

        await telegram_message.reply_text(reply)

    except Exception as e:
        print(f"Error while processing message: {e}")
        import traceback
        traceback.print_exc()

        await telegram_message.reply_text(
            "⚠️ Sorry, something went wrong. Please try again."
        )

def run_bot():

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat,
        )
    )

    print("🤖 Telegram Bot Running...")

    app.run_polling()