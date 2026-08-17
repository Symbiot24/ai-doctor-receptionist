from datetime import date

from sqlalchemy.orm import Session

from app.database.models import Appointment
from app.database.models import Doctor
from app.services.clinic_service import get_current_clinic


class AppointmentRepository:

    def __init__(self, db: Session):

        self.db = db

    # ---------------- Create ---------------- #

    def _resolve_clinic_id(
        self,
        doctor_name,
    ):

        doctor = (
            self.db.query(Doctor)
            .filter(
                Doctor.active == "YES",
                Doctor.name == doctor_name,
            )
            .first()
        )

        if doctor is not None and doctor.clinic_id is not None:

            return doctor.clinic_id

        # Single-clinic system: fall back to the one clinic record.
        # Fails clearly if zero or multiple clinics exist.
        return get_current_clinic(self.db).id

    def create(
        self,
        appointment_data: dict,
    ):

        appointment_data = dict(appointment_data)

        appointment_data.pop("clinic_id", None)

        appointment_data["clinic_id"] = self._resolve_clinic_id(
            appointment_data.get("doctor")
        )

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
        exclude_appointment_id=None,
    ):

        query = (
            self.db.query(Appointment)
            .filter(
                Appointment.doctor == doctor,
                Appointment.appointment_date == appointment_date,
                Appointment.status == "BOOKED",
            )
        )

        if exclude_appointment_id is not None:

            query = query.filter(
                Appointment.id != exclude_appointment_id,
            )

        appointments = query.all()

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