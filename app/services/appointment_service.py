from app.repositories.appointment_repository import AppointmentRepository


class AppointmentService:

    def __init__(self, db):

        self.repository = AppointmentRepository(db)

    def book(self, appointment_data):

        return self.repository.create(
            appointment_data
        )

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