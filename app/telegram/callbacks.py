from telegram import Update
from telegram.ext import ContextTypes

from app.database.db import SessionLocal
from app.services.appointment_service import AppointmentService
from app.flows.booking.flow import BookingFlow
from app.state.state_manager import state_manager
from app.state.booking_state import BookingState

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

    # --------------------------------------------------
    # Doctor Selection
    # --------------------------------------------------

    if data.startswith("doctor:"):

        doctor_name = data.split(":", 1)[1]

        reply = booking_flow.select_doctor(
            user_id,
            doctor_name,
        )

        await query.edit_message_text(reply)

        return

    # --------------------------------------------------
    # Slot Selection
    # --------------------------------------------------

    if data.startswith("slot:"):

        slot = data.split(":", 1)[1]

        session = state_manager.get(user_id)

        if session["state"] == BookingState.ASK_RESCHEDULE_SLOT:

            reply = booking_flow.select_reschedule_slot(
                user_id,
                slot,
            )

        else:

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

    # --------------------------------------------------
    # Cancel Appointment
    # --------------------------------------------------

    if data.startswith("cancel:"):

        appointment_id = data.split(":", 1)[1]

        db = SessionLocal()

        try:

            service = AppointmentService(db)

            appointment = service.cancel(
                appointment_id,
            )

            if appointment is None:

                await query.edit_message_text(
                    "❌ Appointment not found."
                )

                return

            await query.edit_message_text(
                f"""
✅ Appointment Cancelled Successfully

👨‍⚕️ Doctor: {appointment.doctor}

📅 Date: {appointment.appointment_date}

🕒 Time: {appointment.appointment_time.strftime('%H:%M')}

📌 Status: {appointment.status}
"""
            )

        finally:

            db.close()

        return

    # --------------------------------------------------
    # Reschedule Appointment
    # --------------------------------------------------

    if data.startswith("reschedule:"):

        appointment_id = data.split(":", 1)[1]

        reply = booking_flow.start_reschedule(
            user_id,
            appointment_id,
        )

        await query.edit_message_text(reply)

        return