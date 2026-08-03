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

    def my_appointments(
        self,
        telegram_id,
    ):

        return self.repository.get_by_user(
            telegram_id
        )


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
        appointment_id: int,
        telegram_id: str,
    ):

        appointment = self.repository.get_by_id_and_user(
            appointment_id,
            telegram_id,
        )

        if appointment is None:

            return False

        appointment.status = "CANCELLED"

        self.repository.db.commit()

        return True

    def cancel(self, appointment_id):

        return self.repository.cancel(
            appointment_id
        )