from app.state.booking_state import BookingState
from app.state.state_manager import state_manager
from app.flows.booking.validator import BookingValidator
from datetime import datetime

class BookingFlow:

    def start(self, user_id: int):

        state_manager.update_state(
            user_id,
            BookingState.ASK_NAME,
        )

        return "🏥 Let's book your appointment.\n\nWhat is your full name?"

    def handle(self, user_id: int, message: str):

        session = state_manager.get(user_id)

        state = session["state"]

        if state == BookingState.ASK_NAME:

            state_manager.save(
                user_id,
                "patient_name",
                message,
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_PHONE,
            )

            return "📞 Please enter your phone number."

        if state == BookingState.ASK_PHONE:

            valid, error = BookingValidator.validate_phone(message)

            if not valid:
                return error

            state_manager.save(
                user_id,
                "phone",
                message,
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_AGE,
            )

            return "What is your age?"

        if state == BookingState.ASK_AGE:

            valid, error = BookingValidator.validate_age(message)

            if not valid:
                return error

            state_manager.save(
                user_id,
                "age",
                message,
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_GENDER,
            )

            return "What is your gender?"

        if state == BookingState.ASK_GENDER:

            valid, error = BookingValidator.validate_gender(message)

            if not valid:
                return error

            state_manager.save(
                user_id,
                "gender",
                message,
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_SYMPTOMS,
            )

            return "🩺 Please describe your symptoms."

        if state == BookingState.ASK_SYMPTOMS:

            state_manager.save(
                user_id,
                "symptoms",
                message,
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_DOCTOR,
            )

            return "👨‍⚕️ Which doctor would you like to consult?"

        if state == BookingState.ASK_DOCTOR:

            state_manager.save(
                user_id,
                "doctor",
                message,
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_DATE,
            )

            return "📅 Preferred appointment date? (YYYY-MM-DD)"

        if state == BookingState.ASK_DATE:

            valid, error = BookingValidator.validate_date(message)

            if not valid:
                return error

            appointment_date = datetime.strptime(
                message,
                "%Y-%m-%d"
            ).date()

            state_manager.save(
                user_id,
                "appointment_date",
                appointment_date,
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_TIME,
            )

            return "⏰ Preferred appointment time? (HH:MM)"

        if state == BookingState.ASK_TIME:

            valid, error = BookingValidator.validate_time(message)

            if not valid:
                return error

            appointment_time = datetime.strptime(
                message,
                "%H:%M"
            ).time()

            state_manager.save(
                user_id,
                "appointment_time",
                appointment_time,
            )

            state_manager.update_state(
                user_id,
                BookingState.CONFIRM,
            )

            data = session["data"]

            return (
                f"Please confirm your appointment:\n\n"
                f"Name: {data['patient_name']}\n"
                f"Phone: {data['phone']}\n"
                f"Age: {data['age']}\n"
                f"Gender: {data['gender']}\n"
                f"Symptoms: {data['symptoms']}\n"
                f"Doctor: {data['doctor']}\n"
                f"Date: {data['appointment_date']}\n"
                f"Time: {data['appointment_time']}\n\n"
                "Reply YES to confirm or NO to cancel."
            )

        if state == BookingState.CONFIRM:

            if message.lower() != "yes":

                state_manager.reset(user_id)

                return "❌ Appointment cancelled."

        from app.database.db import SessionLocal
        from app.services.appointment_service import AppointmentService

        db = SessionLocal()

        service = AppointmentService(db)

        available = service.check_availability(
            session["data"]["doctor"],
            session["data"]["appointment_date"],
            session["data"]["appointment_time"],
        )

        if not available:

            db.close()

            state_manager.update_state(
                user_id,
                BookingState.ASK_TIME,
            )

            return (
                "❌ This slot is already booked.\n\n"
                "Please enter another appointment time."
            )

        appointment = service.book(
            session["data"]
        )

        db.close()

        state_manager.reset(user_id)

        return (
        "✅ Appointment booked successfully!\n\n"
        f"Appointment ID: {appointment.id}"
        )
