from app.repositories.appointment_repository import AppointmentRepository


class AppointmentService:

    def __init__(self, db):

        self.repository = AppointmentRepository(db)

    def book(self, appointment_data):

        return self.repository.create(
            appointment_data
        )