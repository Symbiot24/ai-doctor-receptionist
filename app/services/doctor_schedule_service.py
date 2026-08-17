from datetime import datetime
from datetime import time

from app.repositories.doctor_repository import DoctorRepository
from app.repositories.doctor_schedule_repository import DoctorScheduleRepository


class DoctorScheduleService:

    WEEKDAYS = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    DAY_NAMES = {
        name.lower(): index
        for index, name in enumerate(WEEKDAYS)
    }

    TIME_FIELDS = (
        "morning_start",
        "morning_end",
        "evening_start",
        "evening_end",
    )

    def __init__(self, db):

        self.db = db

        self.repository = DoctorScheduleRepository(db)

        self.doctor_repository = DoctorRepository(db)

    # ---------------- Normalization ---------------- #

    @classmethod
    def normalize_day_of_week(cls, day_of_week):

        if isinstance(day_of_week, str):

            key = day_of_week.strip().lower()

            if key in cls.DAY_NAMES:

                return cls.DAY_NAMES[key]

            try:

                value = int(key)

            except ValueError:

                raise ValueError(
                    f"Invalid weekday {day_of_week!r}. "
                    f"Use 0-6 or one of {cls.WEEKDAYS}."
                )

        else:

            try:

                value = int(day_of_week)

            except (TypeError, ValueError):

                raise ValueError(
                    f"Invalid weekday {day_of_week!r}. "
                    f"Use 0-6 or one of {cls.WEEKDAYS}."
                )

        if value < 0 or value > 6:

            raise ValueError(
                f"Invalid weekday {value}. Must be between 0 and 6."
            )

        return value

    def _normalize(self, data: dict):

        for field in self.TIME_FIELDS:

            value = data.get(field)

            if isinstance(value, str):

                data[field] = datetime.strptime(value, "%H:%M").time()

            elif value is not None and not isinstance(value, time):

                raise ValueError(
                    f"Invalid time value for {field}. Use 'HH:MM'."
                )

        return data

    # ---------------- Validation ---------------- #

    def validate_schedule(
        self,
        data: dict,
    ) -> list:
        """Return a list of validation error strings (empty when valid).

        Rules:
        - weekday must be 0-6 (or a weekday name)
        - morning start must be before morning end (when both present)
        - evening start must be before evening end (when both present)
        - morning and evening shifts must not overlap
        - morning/evening may be independently disabled; an empty day is valid
        """
        errors = []

        if "day_of_week" in data and data.get("day_of_week") is not None:

            try:

                self.normalize_day_of_week(data["day_of_week"])

            except ValueError as error:

                errors.append(str(error))

        morning_start = data.get("morning_start")
        morning_end = data.get("morning_end")
        evening_start = data.get("evening_start")
        evening_end = data.get("evening_end")

        if morning_start and morning_end:

            if morning_end <= morning_start:

                errors.append(
                    "morning_start/morning_end invalid: "
                    "end must be after start"
                )

        if evening_start and evening_end:

            if evening_end <= evening_start:

                errors.append(
                    "evening_start/evening_end invalid: "
                    "end must be after start"
                )

        if (
            morning_start and morning_end
            and evening_start and evening_end
        ):

            if evening_start < morning_end:

                errors.append(
                    "morning and evening shifts must not overlap"
                )

        return errors

    # ---------------- Queries ---------------- #

    def get_doctor_schedule(
        self,
        doctor_id,
    ):

        return self.repository.get_by_doctor(doctor_id)

    def get_day_schedule(
        self,
        doctor_id,
        day_of_week,
    ):

        day_of_week = self.normalize_day_of_week(day_of_week)

        return self.repository.get_by_doctor_and_day(
            doctor_id,
            day_of_week,
        )

    # ---------------- Save ---------------- #

    def save_day_schedule(
        self,
        doctor_id,
        day_of_week,
        data: dict,
    ):

        if self.doctor_repository.get_by_id(doctor_id) is None:

            raise ValueError(f"Doctor {doctor_id} not found.")

        day_of_week = self.normalize_day_of_week(day_of_week)

        data = dict(data)

        data.pop("doctor_id", None)

        data.pop("day_of_week", None)

        data.pop("id", None)

        data = self._normalize(data)

        errors = self.validate_schedule(
            {
                "day_of_week": day_of_week,
                **data,
            }
        )

        if errors:

            raise ValueError("; ".join(errors))

        schedule = self.repository.get_by_doctor_and_day(
            doctor_id,
            day_of_week,
        )

        if schedule is None:

            return self.repository.create(
                {
                    "doctor_id": doctor_id,
                    "day_of_week": day_of_week,
                    **data,
                }
            )

        return self.repository.update(schedule, data)

    # ---------------- Delete ---------------- #

    def delete_day_schedule(
        self,
        doctor_id,
        day_of_week,
    ):

        day_of_week = self.normalize_day_of_week(day_of_week)

        schedule = self.repository.get_by_doctor_and_day(
            doctor_id,
            day_of_week,
        )

        return self.repository.delete(schedule)