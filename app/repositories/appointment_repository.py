from sqlalchemy.orm import Session

from app.database.models import Appointment


class AppointmentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, appointment_data: dict):

        appointment = Appointment(**appointment_data)

        self.db.add(appointment)

        self.db.commit()

        self.db.refresh(appointment)

        return appointment

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