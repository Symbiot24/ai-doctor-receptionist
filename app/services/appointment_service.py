from app.repositories.appointment_repository import AppointmentRepository
from app.services.slot_service import SlotService


class AppointmentService:

    def __init__(self, db):

        self.db = db

        self.repository = AppointmentRepository(db)

        self.slot_service = SlotService(db)

    # ---------------- Booking ---------------- #

    def book(
        self,
        appointment_data,
    ):

        appointment_data = dict(appointment_data)

        if not self.slot_service.is_slot_available(
            appointment_data.get("doctor"),
            appointment_data.get("appointment_date"),
            appointment_data.get("appointment_time"),
        ):

            raise ValueError("Slot is not available for booking.")

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

        return self.slot_service.is_slot_available(
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

        if not self.slot_service.is_slot_available(
            appointment.doctor,
            appointment_date,
            appointment_time,
            exclude_appointment_id=appointment.id,
        ):

            raise ValueError("New slot is not available.")

        return self.repository.reschedule(
            appointment,
            appointment_date,
            appointment_time,
        )