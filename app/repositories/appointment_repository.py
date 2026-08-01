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