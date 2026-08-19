from datetime import datetime
from datetime import timedelta

from app.repositories.appointment_repository import AppointmentRepository
from app.services.clinic_day_off_service import ClinicDayOffService
from app.services.doctor_day_off_service import DoctorDayOffService
from app.services.doctor_service import DoctorService
from app.services.doctor_schedule_service import DoctorScheduleService


class SlotService:
    """Single source of truth for doctor slot availability.

    Availability rules (identical for new booking, slot display and
    rescheduling):

    1. Doctor exists
    2. Doctor is active
    3. The requested date is not a clinic day-off
    4. Weekly schedule exists for the weekday (or legacy shifts)
    5. That weekday is enabled
    6. The requested date is not a doctor day-off
    7. Time falls inside a morning/evening shift boundary
    8. Existing BOOKED appointments are excluded (CANCELLED never blocks)
    9. Slot duration is respected (no slot that overruns a shift)
    """

    SLOT_DURATION = 30

    DEFAULT_START = "09:00"

    DEFAULT_END = "17:00"

    def __init__(self, db):

        self.repository = AppointmentRepository(db)

        self.doctor_service = DoctorService(db)

        self.schedule_service = DoctorScheduleService(db)

        self.day_off_service = DoctorDayOffService(db)

        self.clinic_day_off_service = ClinicDayOffService(db)

    # ---------------- Helpers ---------------- #

    @staticmethod
    def _to_date(value):

        if isinstance(value, str):

            return datetime.strptime(value, "%Y-%m-%d").date()

        return value

    @staticmethod
    def _to_time(value):

        if isinstance(value, str):

            return datetime.strptime(value, "%H:%M").time()

        return value

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

        # Generate only slots that fit fully inside the shift window:
        # current < end guarantees a full SLOT_DURATION fits before end.
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

    def _filter_shifts(self, shifts):

        return [
            (start, end)
            for start, end in shifts
            if start and end
        ]

    def _resolve_shifts(
        self,
        doctor,
        appointment_date,
    ):
        """Return the active (start, end) shift windows for the date.

        Returns an empty list when the doctor has no availability that day
        (clinic day-off, doctor day-off, disabled weekday, or no
        schedule/shifts configured).
        """
        if self.clinic_day_off_service.is_day_off(
            appointment_date,
        ):
            return []

        if self.day_off_service.is_day_off(
            doctor.id,
            appointment_date,
        ):
            return []

        day_of_week = appointment_date.weekday()

        schedule = self.schedule_service.get_day_schedule(
            doctor.id,
            day_of_week,
        )

        if schedule is not None:

            if not schedule.enabled:
                return []

            return self._filter_shifts(
                [
                    (schedule.morning_start, schedule.morning_end),
                    (schedule.evening_start, schedule.evening_end),
                ]
            )

        shifts = self._filter_shifts(
            self._shifts_from_doctor(doctor)
        )

        if not shifts:

            shifts = [
                (
                    datetime.strptime(self.DEFAULT_START, "%H:%M").time(),
                    datetime.strptime(self.DEFAULT_END, "%H:%M").time(),
                )
            ]

        return shifts

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

    # ---------------- Public API ---------------- #

    def available_slots_for_id(
        self,
        doctor_id,
        appointment_date,
        exclude_appointment_id=None,
    ):
        """Resolve the doctor by id then delegate to available_slots().

        Keeps SlotService the single source of truth while letting the
        admin API address doctors by id. A deactivated doctor resolves to
        no availability (find_by_name only matches active doctors).
        """
        doctor = self.doctor_service.get_by_id(doctor_id)

        if doctor is None:
            return []

        return self.available_slots(
            doctor.name,
            appointment_date,
            exclude_appointment_id=exclude_appointment_id,
        )

    def available_slots(
        self,
        doctor_name,
        appointment_date,
        exclude_appointment_id=None,
    ):

        appointment_date = self._to_date(appointment_date)

        doctor = self.doctor_service.find_by_name(doctor_name)

        if doctor is None:
            return []

        shifts = self._resolve_shifts(doctor, appointment_date)

        if not shifts:
            return []

        booked = self.repository.get_booked_slots(
            doctor_name,
            appointment_date,
            exclude_appointment_id=exclude_appointment_id,
        )

        return self._generate(shifts, booked)

    def unavailability_reason(
        self,
        doctor_name,
        appointment_date,
        exclude_appointment_id=None,
    ):
        """Explain why a date has no available slots for a doctor.

        Returns a human-readable reason string, or ``None`` when the date
        actually has available slots. Used by the booking/reschedule flows
        to give users a specific explanation (clinic closed, doctor on
        leave, day off, etc.) instead of a generic "no slots" message.
        """
        appointment_date = self._to_date(appointment_date)

        doctor = self.doctor_service.find_by_name(doctor_name)

        if doctor is None:
            return f"❌ No doctor found named '{doctor_name}'."

        day_label = appointment_date.strftime("%A, %d %B %Y")

        if self.clinic_day_off_service.is_day_off(appointment_date):
            return (
                f"❌ The clinic is closed on {day_label}.\n"
                "Please choose another date."
            )

        if self.day_off_service.is_day_off(doctor.id, appointment_date):
            return (
                f"❌ {doctor.name} is on leave on {day_label}.\n"
                "Please choose another date."
            )

        day_of_week = appointment_date.weekday()

        schedule = self.schedule_service.get_day_schedule(
            doctor.id,
            day_of_week,
        )

        if schedule is not None and not schedule.enabled:
            return (
                f"❌ {doctor.name} is not available on "
                f"{appointment_date.strftime('%A')}.\n"
                "Please choose another date."
            )

        shifts = self._resolve_shifts(doctor, appointment_date)

        if not shifts:
            return (
                f"❌ {doctor.name} has no consultation hours on {day_label}.\n"
                "Please choose another date."
            )

        booked = self.repository.get_booked_slots(
            doctor_name,
            appointment_date,
            exclude_appointment_id=exclude_appointment_id,
        )

        if not self._generate(shifts, booked):
            return (
                f"❌ All slots are already booked on {day_label}.\n"
                "Please choose another date."
            )

        return None

    def is_slot_available(
        self,
        doctor_name,
        appointment_date,
        appointment_time,
        exclude_appointment_id=None,
    ):

        appointment_date = self._to_date(appointment_date)

        appointment_time = self._to_time(appointment_time)

        doctor = self.doctor_service.find_by_name(doctor_name)

        if doctor is None:
            return False

        shifts = self._resolve_shifts(doctor, appointment_date)

        if not shifts:
            return False

        # The requested time must be a slot start that fits inside a shift.
        candidates = self._generate(shifts, booked=set())

        if appointment_time.strftime("%H:%M") not in candidates:
            return False

        booked = self.repository.get_booked_slots(
            doctor_name,
            appointment_date,
            exclude_appointment_id=exclude_appointment_id,
        )

        return appointment_time not in booked