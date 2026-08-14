from datetime import datetime
from datetime import timedelta

from app.repositories.appointment_repository import AppointmentRepository
from app.services.doctor_service import DoctorService
from app.services.doctor_schedule_service import DoctorScheduleService


class SlotService:

    SLOT_DURATION = 30

    DEFAULT_START = "09:00"

    DEFAULT_END = "17:00"

    def __init__(self, db):

        self.repository = AppointmentRepository(db)

        self.doctor_service = DoctorService(db)

        self.schedule_service = DoctorScheduleService(db)

    def _window_slots(
        self,
        start_time,
        end_time,
        booked,
    ):

        slots = []

        if not start_time or not end_time:
            return slots

        current = datetime.combine(
            datetime.now().date(),
            start_time,
        )

        end = datetime.combine(
            datetime.now().date(),
            end_time,
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

    def _shifts_from_doctor(self, doctor):

        return [
            (doctor.morning_start, doctor.morning_end),
            (doctor.evening_start, doctor.evening_end),
        ]

    def _generate(
        self,
        shifts,
        booked,
    ):

        slots = []

        for start_time, end_time in shifts:

            slots.extend(
                self._window_slots(
                    start_time,
                    end_time,
                    booked,
                )
            )

        return slots

    def available_slots(
        self,
        doctor_name,
        appointment_date,
    ):

        if isinstance(appointment_date, str):

            appointment_date = datetime.strptime(
                appointment_date,
                "%Y-%m-%d",
            ).date()

        booked = self.repository.get_booked_slots(
            doctor_name,
            appointment_date,
        )

        doctor = self.doctor_service.find_by_name(doctor_name)

        if doctor is None:
            return []

        day_of_week = appointment_date.weekday()

        schedule = self.schedule_service.get_day_schedule(
            doctor.id,
            day_of_week,
        )

        # Weekly schedule takes priority when it exists.
        if schedule is not None:

            if not schedule.enabled:
                return []

            shifts = [
                (schedule.morning_start, schedule.morning_end),
                (schedule.evening_start, schedule.evening_end),
            ]

            return self._generate(shifts, booked)

        # No schedule record yet: fall back to the doctor's legacy
        # morning/evening shift fields so existing booking keeps working.
        slots = self._generate(
            self._shifts_from_doctor(doctor),
            booked,
        )

        # Fall back to a default window if the doctor has no
        # shift timings configured yet (e.g. pre-migration).
        if not slots and not (
            doctor.morning_start or doctor.evening_start
        ):

            slots = self._window_slots(
                datetime.strptime(self.DEFAULT_START, "%H:%M").time(),
                datetime.strptime(self.DEFAULT_END, "%H:%M").time(),
                booked,
            )

        return slots