from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from app.core.config import TELEGRAM_BOT_TOKEN
from app.agent.ai_service import generate_reply

from app.router.intent_extractor import IntentExtractor

from app.telegram.appointment_keyboard import appointment_actions
from app.flows.booking.flow import BookingFlow

from app.state.state_manager import state_manager
from app.state.booking_state import BookingState

from app.telegram.callbacks import callback_handler

from app.database.db import SessionLocal
from app.services.appointment_service import AppointmentService

booking_flow = BookingFlow()


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "🏥 Welcome to AI Doctor Appointment System!\n\n"
        "I can help you:\n\n"
        "• Book Appointment\n"
        "• View My Appointments\n"
        "• Cancel Appointment\n"
        "• Reschedule Appointment\n\n"
        "Just tell me naturally what you need.\n\n"
        "Examples:\n"
        "• I want to book an appointment tomorrow.\n"
        "• Show my appointments.\n"
        "• Cancel my appointment.\n"
        "• I need to reschedule."
    )


async def chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    telegram_message = update.effective_message

    if telegram_message is None:
        return

    if telegram_message.text is None:
        return

    user_id = update.effective_user.id

    message = telegram_message.text.strip()

    session = state_manager.get(user_id)

    try:

        # Continue active booking/reschedule flow
        if session["state"] != BookingState.IDLE:

            reply = booking_flow.handle(
                user_id,
                message,
            )

        else:

            result = IntentExtractor.extract(message)

            intent = result.get("intent")
            entities = result.get("entities", {})

            print("=" * 60)
            print("Intent :", intent)
            print("Entities :", entities)
            print("=" * 60)

            # ---------------- BOOK ----------------

            if intent == "BOOK_APPOINTMENT":

                reply = booking_flow.start(
                    user_id,
                    entities,
                )

            # ------------ VIEW APPOINTMENTS ------------

            elif intent == "VIEW_APPOINTMENTS":

                db = SessionLocal()

                service = AppointmentService(db)

                appointments = service.my_appointments(
                    str(user_id)
                )

                db.close()

                if not appointments:

                    reply = (
                        "📭 You don't have any upcoming appointments."
                    )

                else:

                    for appointment in appointments:

                        await telegram_message.reply_text(
                            f"""
🆔 Appointment #{appointment.id}

👨‍⚕️ Doctor: {appointment.doctor}

📅 Date: {appointment.appointment_date}

🕒 Time: {appointment.appointment_time.strftime('%H:%M')}

📌 Status: {appointment.status}
""",
                            reply_markup=appointment_actions(
                                appointment.id
                            ),
                        )

                    reply = None

            # ------------ CANCEL ------------

            elif intent == "CANCEL_APPOINTMENT":

                db = SessionLocal()

                service = AppointmentService(db)

                appointments = service.my_appointments(
                    str(user_id)
                )

                db.close()

                if not appointments:

                    reply = "📭 You don't have any appointments."

                else:

                    for appointment in appointments:

                        await telegram_message.reply_text(
                            f"""
🆔 Appointment #{appointment.id}

👨‍⚕️ Doctor: {appointment.doctor}

📅 Date: {appointment.appointment_date}

🕒 Time: {appointment.appointment_time.strftime('%H:%M')}
""",
                            reply_markup=appointment_actions(
                                appointment.id
                            ),
                        )

                    reply = None

            # ------------ RESCHEDULE ------------

            elif intent == "RESCHEDULE_APPOINTMENT":

                db = SessionLocal()

                service = AppointmentService(db)

                appointments = service.my_appointments(
                    str(user_id)
                )

                db.close()

                if not appointments:

                    reply = "📭 You don't have any appointments."

                else:

                    for appointment in appointments:

                        await telegram_message.reply_text(
                            f"""
🆔 Appointment #{appointment.id}

👨‍⚕️ Doctor: {appointment.doctor}

📅 Date: {appointment.appointment_date}

🕒 Time: {appointment.appointment_time.strftime('%H:%M')}
""",
                            reply_markup=appointment_actions(
                                appointment.id
                            ),
                        )

                    reply = None

            # ------------ GENERAL CHAT ------------

            else:

                reply = generate_reply(
                    user_id,
                    message,
                )

        # ---------------- SEND RESPONSE ----------------

        if reply is None:
            return

        if isinstance(reply, tuple):

            text, keyboard = reply

            await telegram_message.reply_text(
                text=text,
                reply_markup=keyboard,
            )

        else:

            await telegram_message.reply_text(reply)

    except Exception as e:

        print(f"Error while processing message: {e}")

        import traceback

        traceback.print_exc()

        await telegram_message.reply_text(
            "⚠️ Sorry, something went wrong."
        )


def run_bot():

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            callback_handler,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat,
        )
    )

    print("🤖 Telegram Bot Running...")

    app.run_polling()