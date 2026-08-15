from datetime import date
from datetime import datetime

from app.repositories.doctor_day_off_repository import DoctorDayOffRepository
from app.repositories.doctor_repository import DoctorRepository


class DoctorDayOffService:

    def __init__(self, db):

        self.db = db

        self.repository = DoctorDayOffRepository(db)

        self.doctor_repository = DoctorRepository(db)

    # ---------------- Normalization ---------------- #

    @staticmethod
    def normalize_date(value):

        if isinstance(value, date):

            return value

        if isinstance(value, str):

            try:

                return datetime.strptime(value.strip(), "%Y-%m-%d").date()

            except ValueError:

                raise ValueError(
                    f"Invalid date {value!r}. Use 'YYYY-MM-DD'."
                )

        raise ValueError(
            f"Invalid date {value!r}. Use 'YYYY-MM-DD'."
        )

    # ---------------- Queries ---------------- #

    def get_day_offs(
        self,
        doctor_id,
    ):

        return self.repository.get_by_doctor(doctor_id)

    def is_day_off(
        self,
        doctor_id,
        date,
    ):

        date = self.normalize_date(date)

        return self.repository.exists(doctor_id, date)

    # ---------------- Create / Delete ---------------- #

    def add_day_off(
        self,
        doctor_id,
        date,
        reason=None,
    ):

        doctor = self.doctor_repository.get_by_id(doctor_id)

        if doctor is None:

            raise ValueError(f"Doctor {doctor_id} not found.")

        date = self.normalize_date(date)

        if self.repository.exists(doctor_id, date):

            raise ValueError(
                f"Doctor {doctor_id} already has a day off on {date}."
            )

        return self.repository.create(
            {
                "doctor_id": doctor_id,
                "date": date,
                "reason": reason,
            }
        )

    def remove_day_off(
        self,
        doctor_id,
        date,
    ):

        date = self.normalize_date(date)

        day_off = self.repository.get_by_doctor_and_date(
            doctor_id,
            date,
        )

        return self.repository.delete(day_off)