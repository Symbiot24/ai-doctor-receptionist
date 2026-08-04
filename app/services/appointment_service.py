from app.repositories.appointment_repository import AppointmentRepository


class AppointmentService:

    def __init__(self, db):

        self.repository = AppointmentRepository(db)

    # ---------------- Booking ---------------- #

    def book(
        self,
        appointment_data,
    ):

        return self.repository.create(
            appointment_data
        )

    # ---------------- Availability ---------------- #

    def check_availability(
        self,
        doctor,
        appointment_date,
        appointment_time,
    ):

        return self.repository.is_slot_available(
            doctor,
            appointment_date,
            appointment_time,
        )

    # ---------------- My Appointments ---------------- #

    def my_appointments(
        self,
        telegram_id,
    ):

        return self.repository.get_by_user(
            telegram_id
        )

    # ---------------- Get Appointment ---------------- #

    def get_by_id(
        self,
        appointment_id,
    ):

        return self.repository.get_by_id(
            appointment_id
        )

    # ---------------- Cancel ---------------- #

    def cancel(
        self,
        appointment_id,
    ):

        appointment = self.repository.get_by_id(
            appointment_id
        )

        if appointment is None:
            return None

        return self.repository.cancel(
            appointment
        )

    def cancel_by_user(
        self,
        appointment_id,
        telegram_id,
    ):

        appointment = self.repository.get_by_id_and_user(
            appointment_id,
            telegram_id,
        )

        if appointment is None:
            return False

        appointment.status = "CANCELLED"

        self.repository.db.commit()

        self.repository.db.refresh(appointment)

        return appointment

    # ---------------- Reschedule ---------------- #

    def reschedule(
        self,
        appointment_id,
        appointment_date,
        appointment_time,
    ):

        appointment = self.repository.get_by_id(
            appointment_id
        )

        if appointment is None:
            return None

        return self.repository.reschedule(
            appointment,
            appointment_date,
            appointment_time,
        )