from datetime import datetime
from app.services.slot_service import SlotService
from app.database.db import SessionLocal
from app.flows.booking.validator import BookingValidator
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService
from app.state.booking_state import BookingState
from app.telegram.keyboards import doctor_keyboard
from app.state.state_manager import state_manager
from app.telegram.keyboards import slot_keyboard


class BookingFlow:

    def start(self, user_id: int):

        state_manager.update_state(
            user_id,
            BookingState.ASK_NAME,
        )

        return (
            "🏥 Let's book your appointment.\n\n"
            "What is your full name?"
        )

    def handle(self, user_id: int, message: str):

        session = state_manager.get(user_id)

        state = session["state"]

        # ---------------- ASK NAME ---------------- #

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

        # ---------------- ASK PHONE ---------------- #

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

            return "🎂 What is your age?"

        # ---------------- ASK AGE ---------------- #

        if state == BookingState.ASK_AGE:

            valid, error = BookingValidator.validate_age(message)

            if not valid:
                return error

            state_manager.save(
                user_id,
                "age",
                int(message),
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_GENDER,
            )

            return "👤 What is your gender?"

        # ---------------- ASK GENDER ---------------- #

        if state == BookingState.ASK_GENDER:

            valid, error = BookingValidator.validate_gender(message)

            if not valid:
                return error

            state_manager.save(
                user_id,
                "gender",
                message.title(),
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_SYMPTOMS,
            )

            return "🩺 Please describe your symptoms."

        # ---------------- ASK SYMPTOMS ---------------- #

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

            db = SessionLocal()

            doctor_service = DoctorService(db)

            doctors = doctor_service.get_all()

            db.close()

            return (
                "👨‍⚕️ Please select a doctor:",
                doctor_keyboard(doctors),
            )

        # ---------------- ASK DOCTOR ---------------- #

        if state == BookingState.ASK_DOCTOR:

            db = SessionLocal()

            doctor_service = DoctorService(db)

            doctor = doctor_service.exists(
                message.strip().title()
            )

            db.close()

            if doctor is None:

                return (
                    "❌ Doctor not found.\n\n"
                    "Please enter one of the available doctors."
                )

            state_manager.save(
                user_id,
                "doctor",
                doctor.name,
            )

            state_manager.update_state(
                user_id,
                BookingState.ASK_DATE,
            )

            return "📅 Preferred appointment date? (YYYY-MM-DD)"


        # ---------------- RESCHEDULE DATE ---------------- #

        if state == BookingState.ASK_RESCHEDULE_DATE:

            valid, error = BookingValidator.validate_date(message)

            if not valid:
                return error

            appointment_date = datetime.strptime(
                message,
                "%Y-%m-%d",
            ).date()

            state_manager.save(
                user_id,
                "appointment_date",
                appointment_date,
            )

            db = SessionLocal()

            appointment_service = AppointmentService(db)

            appointment = appointment_service.get_by_id(
                session["data"]["appointment_id"]
            )

            if appointment is None or str(appointment.telegram_id) != str(user_id):

                db.close()

                state_manager.reset(user_id)

                return "❌ Appointment not found or access denied."

            state_manager.save(
                user_id,
                "doctor",
                appointment.doctor,
            )

            slot_service = SlotService(db)

            slots = slot_service.available_slots(
                appointment.doctor,
                appointment_date,
            )

            db.close()

            if not slots:

                return (
                    "❌ No slots available.\n\n"
                    "Please choose another date."
                )

            state_manager.update_state(
                user_id,
                BookingState.ASK_RESCHEDULE_SLOT,
            )

            return (
                "🕒 Select a new slot:",
                slot_keyboard(slots),
            )

        # ---------------- ASK DATE ---------------- #

        if state == BookingState.ASK_DATE:

            valid, error = BookingValidator.validate_date(message)

            if not valid:
                return error

            appointment_date = datetime.strptime(
                message,
                "%Y-%m-%d",
            ).date()

            state_manager.save(
                user_id,
                "appointment_date",
                appointment_date,
            )

            db = SessionLocal()

            slot_service = SlotService(db)

            slots = slot_service.available_slots(
                session["data"]["doctor"],
                appointment_date,
            )

            db.close()

            if not slots:

                return (
                    "❌ No slots available.\n"
                    "Choose another date."
                )

            state_manager.update_state(
                user_id,
                BookingState.ASK_TIME,
            )

            return (
                "🕒 Please select an available slot:",
                slot_keyboard(slots),
            )

        # ---------------- ASK TIME ---------------- #

        if state == BookingState.ASK_TIME:

            valid, error = BookingValidator.validate_time(message)

            if not valid:
                return error

            appointment_time = datetime.strptime(
                message,
                "%H:%M",
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

        # ---------------- CONFIRM ---------------- #

        if state == BookingState.CONFIRM:

            if message.lower() != "yes":

                state_manager.reset(user_id)

                return "❌ Appointment cancelled."

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

            session["data"]["telegram_id"] = str(user_id)

            appointment = service.book(
                session["data"]
            )

            db.close()

            state_manager.reset(user_id)

            return (
                "✅ Appointment booked successfully!\n\n"
                f"Appointment ID: {appointment.id}"
            )

        return "Something went wrong. Please try again."

    def select_doctor(self, user_id: int, doctor_name: str):

        state_manager.save(
            user_id,
            "doctor",
            doctor_name,
        )

        state_manager.update_state(
            user_id,
            BookingState.ASK_DATE,
        )

        return "📅 Select your preferred appointment date (YYYY-MM-DD)."


    def select_slot(self, user_id: int, slot: str):

        appointment_time = datetime.strptime(
            slot,
            "%H:%M",
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

        data = state_manager.get(user_id)["data"]

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
            "Reply YES to confirm."
        )

    def start_reschedule(
        self,
        user_id: int,
        appointment_id: str,
    ):

        session = state_manager.get(user_id)

        session["data"]["appointment_id"] = int(appointment_id)

        state_manager.update_state(
            user_id,
            BookingState.ASK_RESCHEDULE_DATE,
        )

        return (
            "📅 Enter your new appointment date.\n\n"
            "Format: YYYY-MM-DD"
        )


    def select_reschedule_slot(
        self,
        user_id: int,
        slot: str,
    ):

        appointment_time = datetime.strptime(
            slot,
            "%H:%M",
        ).time()

        state_manager.save(
            user_id,
            "appointment_time",
            appointment_time,
        )

        db = SessionLocal()

        service = AppointmentService(db)

        available = service.check_availability(
            state_manager.get(user_id)["data"]["doctor"],
            state_manager.get(user_id)["data"]["appointment_date"],
            appointment_time,
        )

        if not available:

            db.close()

            return (
                "❌ This slot has already been booked.\n"
                "Please choose another slot."
            )

        appointment = service.reschedule(
            appointment_id=state_manager.get(user_id)["data"]["appointment_id"],
            appointment_date=state_manager.get(user_id)["data"]["appointment_date"],
            appointment_time=appointment_time,
        )

        db.close()

        state_manager.reset(user_id)

        return (
            "✅ Appointment Rescheduled Successfully.\n\n"
            f"📅 Date: {appointment.appointment_date}\n"
            f"🕒 Time: {appointment.appointment_time.strftime('%H:%M')}"
        )