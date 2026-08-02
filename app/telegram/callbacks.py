from telegram import Update
from telegram.ext import ContextTypes
from app.database.db import SessionLocal
from app.services.appointment_service import AppointmentService
from app.flows.booking.flow import BookingFlow

booking_flow = BookingFlow()


async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    user_id = update.effective_user.id

    data = query.data

    # ---------------- Doctor Selection ---------------- #

    if data.startswith("doctor:"):

        doctor_name = data.split(":", 1)[1]

        reply = booking_flow.select_doctor(
            user_id,
            doctor_name,
        )

        await query.edit_message_text(reply)

        return

    # ---------------- Slot Selection ---------------- #

    if data.startswith("slot:"):

        slot = data.split(":", 1)[1]

        reply = booking_flow.select_slot(
            user_id,
            slot,
        )

        if isinstance(reply, tuple):

            text, keyboard = reply

            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
            )

        else:

            await query.edit_message_text(reply)

        return

    if data.startswith("cancel:"):

        appointment_id = int(
            data.split(":")[1]
        )

        db = SessionLocal()

        service = AppointmentService(db)

        cancelled = service.cancel_by_user(
            appointment_id,
            str(user_id),
        )

        db.close()

        if cancelled:

            await query.edit_message_text(
                "✅ Appointment cancelled successfully."
            )

        else:

            await query.edit_message_text(
                "❌ Appointment not found."
            )

        return