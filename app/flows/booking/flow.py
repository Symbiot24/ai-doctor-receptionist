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
    
    def _auto_advance(self, user_id: int) -> str | tuple | None:
        """Auto-advance through states where data is already present.
        
        Returns a response message if we reach a state that needs user input,
        or None if we can continue auto-advancing.
        """
        session = state_manager.get(user_id)
        state = session["state"]
        data = session["data"]
        
        # Prevent infinite loops
        for _ in range(20):
            if state == BookingState.ASK_NAME:
                if data.get("patient_name"):
                    state_manager.update_state(user_id, BookingState.ASK_PHONE)
                    state = BookingState.ASK_PHONE
                    continue
                break
                
            elif state == BookingState.ASK_PHONE:
                if data.get("phone"):
                    state_manager.update_state(user_id, BookingState.ASK_AGE)
                    state = BookingState.ASK_AGE
                    continue
                break
                
            elif state == BookingState.ASK_AGE:
                if data.get("age"):
                    state_manager.update_state(user_id, BookingState.ASK_GENDER)
                    state = BookingState.ASK_GENDER
                    continue
                break
                
            elif state == BookingState.ASK_GENDER:
                if data.get("gender"):
                    state_manager.update_state(user_id, BookingState.ASK_SYMPTOMS)
                    state = BookingState.ASK_SYMPTOMS
                    continue
                break
                
            elif state == BookingState.ASK_SYMPTOMS:
                if data.get("symptoms"):
                    state_manager.update_state(user_id, BookingState.ASK_DOCTOR)
                    state = BookingState.ASK_DOCTOR
                    continue
                break
                
            elif state == BookingState.ASK_DOCTOR:
                if data.get("doctor"):
                    state_manager.update_state(user_id, BookingState.ASK_DATE)
                    state = BookingState.ASK_DATE
                    continue
                break
                
            elif state == BookingState.ASK_DATE:
                if data.get("appointment_date"):
                    # Check if we have doctor and slots
                    if data.get("doctor"):
                        db = SessionLocal()
                        try:
                            slot_service = SlotService(db)
                            slots = slot_service.available_slots(
                                data["doctor"],
                                data["appointment_date"],
                            )
                        finally:
                            db.close()
                        
                        if slots:
                            state_manager.update_state(user_id, BookingState.ASK_TIME)
                            state = BookingState.ASK_TIME
                            continue
                        else:
                            # No slots available, stop at ASK_DATE to ask for new date
                            break
                    else:
                        # No doctor yet, stop at ASK_DATE
                        break
                else:
                    break
                    
            elif state == BookingState.ASK_TIME:
                if data.get("appointment_time"):
                    state_manager.update_state(user_id, BookingState.CONFIRM)
                    state = BookingState.CONFIRM
                    continue
                break
                
            elif state == BookingState.CONFIRM:
                # We've reached confirmation, show confirmation message
                break
                
            else:
                # Unknown state, break
                break
        
        # If we ended up at CONFIRM state, return confirmation message
        if state == BookingState.CONFIRM:
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
                "Reply YES to confirm or NO to cancel."
            )
        
        # If we ended up at ASK_TIME with slots available, show slot keyboard
        if state == BookingState.ASK_TIME and data.get("appointment_date") and data.get("doctor"):
            db = SessionLocal()
            try:
                slot_service = SlotService(db)
                slots = slot_service.available_slots(
                    data["doctor"],
                    data["appointment_date"],
                )
            finally:
                db.close()
            
            if slots:
                return (
                    "🕒 Please select an available slot:",
                    slot_keyboard(slots),
                )
        
        # If we ended up at ASK_DOCTOR, show doctor keyboard
        if state == BookingState.ASK_DOCTOR:
            db = SessionLocal()
            try:
                doctor_service = DoctorService(db)
                doctors = doctor_service.get_all()
            finally:
                db.close()
            
            return (
                "👨‍⚕️ Please select a doctor:",
                doctor_keyboard(doctors),
            )
        
        # Return None to indicate we should continue with normal flow
        return None
    
    def _auto_advance(self, user_id: int) -> str | tuple | None:
        """Auto-advance through states where data is already present.
        
        Returns a response message if we reach a state that needs user input,
        or None if we can continue auto-advancing.
        """
        session = state_manager.get(user_id)
        state = session["state"]
        data = session["data"]
        
        # Prevent infinite loops
        for _ in range(20):
            if state == BookingState.ASK_NAME:
                if data.get("patient_name"):
                    state_manager.update_state(user_id, BookingState.ASK_PHONE)
                    state = BookingState.ASK_PHONE
                    continue
                break
                
            elif state == BookingState.ASK_PHONE:
                if data.get("phone"):
                    state_manager.update_state(user_id, BookingState.ASK_AGE)
                    state = BookingState.ASK_AGE
                    continue
                break
                
            elif state == BookingState.ASK_AGE:
                if data.get("age"):
                    state_manager.update_state(user_id, BookingState.ASK_GENDER)
                    state = BookingState.ASK_GENDER
                    continue
                break
                
            elif state == BookingState.ASK_GENDER:
                if data.get("gender"):
                    state_manager.update_state(user_id, BookingState.ASK_SYMPTOMS)
                    state = BookingState.ASK_SYMPTOMS
                    continue
                break
                
            elif state == BookingState.ASK_SYMPTOMS:
                if data.get("symptoms"):
                    state_manager.update_state(user_id, BookingState.ASK_DOCTOR)
                    state = BookingState.ASK_DOCTOR
                    continue
                break
                
            elif state == BookingState.ASK_DOCTOR:
                if data.get("doctor"):
                    state_manager.update_state(user_id, BookingState.ASK_DATE)
                    state = BookingState.ASK_DATE
                    continue
                break
                
            elif state == BookingState.ASK_DATE:
                if data.get("appointment_date"):
                    # Check if we have doctor and slots
                    if data.get("doctor"):
                        db = SessionLocal()
                        try:
                            slot_service = SlotService(db)
                            slots = slot_service.available_slots(
                                data["doctor"],
                                data["appointment_date"],
                            )
                        finally:
                            db.close()
                        
                        if slots:
                            state_manager.update_state(user_id, BookingState.ASK_TIME)
                            state = BookingState.ASK_TIME
                            # Return slot keyboard for user to select
                            return (
                                "🕒 Please select an available slot:",
                                slot_keyboard(slots),
                            )
                        else:
                            # No slots available, ask for different date
                            state_manager.update_state(user_id, BookingState.ASK_DATE)
                            state = BookingState.ASK_DATE
                            return (
                                "❌ No slots available for this date.\n"
                                "Please choose another date."
                            )
                    else:
                        # No doctor yet, stay at ASK_DATE to ask for doctor first
                        state_manager.update_state(user_id, BookingState.ASK_DOCTOR)
                        state = BookingState.ASK_DOCTOR
                        break
                else:
                    break
                    
            elif state == BookingState.ASK_TIME:
                if data.get("appointment_time"):
                    state_manager.update_state(user_id, BookingState.CONFIRM)
                    state = BookingState.CONFIRM
                    continue
                break
                
            elif state == BookingState.CONFIRM:
                # All data collected, show confirmation
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
                
            else:
                # Unknown state or RESCHEDULE states - don't auto-advance
                break
        
        # If we've gone through the loop and haven't returned, 
        # we're at a state that needs user input
        return None

    def start(
        self,
        user_id: int,
        entities: dict | None = None,
    ):

        entities = entities or {}

        state_manager.reset(user_id)

        # ---------------- Name ----------------
        if entities.get("patient_name"):
            state_manager.save(
                user_id,
                "patient_name",
                entities["patient_name"],
            )
        else:
            state_manager.update_state(
                user_id,
                BookingState.ASK_NAME,
            )
            return (
                "🏥 Let's book your appointment.\n\n"
                "What is your full name?"
            )

        # ---------------- Phone ----------------
        if entities.get("phone"):
            state_manager.save(
                user_id,
                "phone",
                entities["phone"],
            )
        else:
            state_manager.update_state(
                user_id,
                BookingState.ASK_PHONE,
            )
            return "📞 Please enter your phone number."

        # ---------------- Age ----------------
        if entities.get("age"):
            state_manager.save(
                user_id,
                "age",
                int(entities["age"]),
            )
        else:
            state_manager.update_state(
                user_id,
                BookingState.ASK_AGE,
            )
            return "🎂 What is your age?"

        # ---------------- Gender ----------------
        if entities.get("gender"):
            state_manager.save(
                user_id,
                "gender",
                entities["gender"].title(),
            )
        else:
            state_manager.update_state(
                user_id,
                BookingState.ASK_GENDER,
            )
            return "👤 What is your gender?"

        # ---------------- Symptoms ----------------
        if entities.get("symptoms"):
            state_manager.save(
                user_id,
                "symptoms",
                entities["symptoms"],
            )
        else:
            state_manager.update_state(
                user_id,
                BookingState.ASK_SYMPTOMS,
            )
            return "🩺 Please describe your symptoms."

        # ---------------- Doctor ----------------
        if entities.get("doctor"):
            # Verify doctor exists using fuzzy matching
            db = SessionLocal()
            try:
                doctor_service = DoctorService(db)
                doctor = doctor_service.find_by_name(entities["doctor"])
                if doctor:
                    state_manager.save(user_id, "doctor", doctor.name)
                else:
                    # If not found, still save the raw input for handle() to deal with
                    state_manager.save(user_id, "doctor", entities["doctor"])
            finally:
                db.close()
        else:
            state_manager.update_state(
                user_id,
                BookingState.ASK_DOCTOR,
            )
            db = SessionLocal()
            try:
                doctor_service = DoctorService(db)
                doctors = doctor_service.get_all()
            finally:
                db.close()
            return (
                "👨‍⚕️ Please select a doctor:",
                doctor_keyboard(doctors),
            )

        # ---------------- Appointment Date ----------------
        if entities.get("appointment_date"):
            # Validate date format
            date_str = entities["appointment_date"]
            try:
                appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                state_manager.save(user_id, "appointment_date", appointment_date)
            except ValueError:
                state_manager.update_state(
                    user_id,
                    BookingState.ASK_DATE,
                )
                return "Please enter appointment date (YYYY-MM-DD)."
        else:
            state_manager.update_state(
                user_id,
                BookingState.ASK_DATE,
            )
            return "Preferred appointment date? (YYYY-MM-DD)"

        # ---------------- Appointment Time ----------------
        if entities.get("appointment_time"):
            # Validate time format
            time_str = entities["appointment_time"]
            try:
                appointment_time = datetime.strptime(time_str, "%H:%M").time()
                state_manager.save(user_id, "appointment_time", appointment_time)
            except ValueError:
                state_manager.update_state(
                    user_id,
                    BookingState.ASK_TIME,
                )
                return "Please enter appointment time (HH:MM)."
        else:
            state_manager.update_state(
                user_id,
                BookingState.ASK_TIME,
            )
            return "Please select an available slot."

        # All fields provided, go to confirmation
        state_manager.update_state(user_id, BookingState.CONFIRM)
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
            "Reply YES to confirm or NO to cancel."
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