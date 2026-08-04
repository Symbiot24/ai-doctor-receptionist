from datetime import date

from sqlalchemy.orm import Session

from app.database.models import Appointment


class AppointmentRepository:

    def __init__(self, db: Session):

        self.db = db

    # ---------------- Create ---------------- #

    def create(
        self,
        appointment_data: dict,
    ):

        appointment = Appointment(**appointment_data)

        self.db.add(appointment)

        self.db.commit()

        self.db.refresh(appointment)

        return appointment

    # ---------------- Availability ---------------- #

    def is_slot_available(
        self,
        doctor: str,
        appointment_date,
        appointment_time,
    ):

        appointment = (
            self.db.query(Appointment)
            .filter(
                Appointment.doctor == doctor,
                Appointment.appointment_date == appointment_date,
                Appointment.appointment_time == appointment_time,
                Appointment.status == "BOOKED",
            )
            .first()
        )

        return appointment is None

    def get_booked_slots(
        self,
        doctor: str,
        appointment_date: date,
    ):

        appointments = (
            self.db.query(Appointment)
            .filter(
                Appointment.doctor == doctor,
                Appointment.appointment_date == appointment_date,
                Appointment.status == "BOOKED",
            )
            .all()
        )

        return [
            appointment.appointment_time
            for appointment in appointments
        ]

    # ---------------- Queries ---------------- #

    def get_by_user(
        self,
        telegram_id: str,
    ):

        return (
            self.db.query(Appointment)
            .filter(
                Appointment.telegram_id == telegram_id,
                Appointment.status == "BOOKED",
            )
            .order_by(
                Appointment.appointment_date,
                Appointment.appointment_time,
            )
            .all()
        )

    def get_by_id(
        self,
        appointment_id,
    ):

        return (
            self.db.query(Appointment)
            .filter(
                Appointment.id == appointment_id,
            )
            .first()
        )

    def get_by_id_and_user(
        self,
        appointment_id,
        telegram_id,
    ):

        return (
            self.db.query(Appointment)
            .filter(
                Appointment.id == appointment_id,
                Appointment.telegram_id == telegram_id,
            )
            .first()
        )

    # ---------------- Cancel ---------------- #

    def cancel(
        self,
        appointment,
    ):

        if appointment is None:
            return None

        if appointment.status == "CANCELLED":
            return appointment

        appointment.status = "CANCELLED"

        self.db.commit()

        self.db.refresh(appointment)

        return appointment

    # ---------------- Reschedule ---------------- #

    def reschedule(
        self,
        appointment,
        appointment_date,
        appointment_time,
    ):

        appointment.appointment_date = appointment_date

        appointment.appointment_time = appointment_time

        self.db.commit()

        self.db.refresh(appointment)

        return appointment