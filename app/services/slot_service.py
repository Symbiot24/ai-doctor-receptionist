from datetime import datetime
from datetime import timedelta

from app.repositories.appointment_repository import AppointmentRepository


class SlotService:

    SLOT_DURATION = 30

    START_HOUR = 9

    END_HOUR = 17

    def __init__(self, db):

        self.repository = AppointmentRepository(db)

    def available_slots(
        self,
        doctor,
        appointment_date,
    ):

        booked = self.repository.get_booked_slots(
            doctor,
            appointment_date,
        )

        slots = []

        current = datetime.combine(
            appointment_date,
            datetime.strptime("09:00", "%H:%M").time(),
        )

        end = datetime.combine(
            appointment_date,
            datetime.strptime("17:00", "%H:%M").time(),
        )

        while current < end:

            slot = current.time()

            if slot not in booked:

                slots.append(
                    slot.strftime("%H:%M")
                )

            current += timedelta(
                minutes=self.SLOT_DURATION
            )

        return slots