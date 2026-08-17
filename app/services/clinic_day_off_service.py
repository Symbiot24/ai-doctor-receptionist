from datetime import date
from datetime import datetime

from app.repositories.clinic_day_off_repository import ClinicDayOffRepository


class ClinicDayOffService:

    def __init__(self, db):

        self.db = db

        self.repository = ClinicDayOffRepository(db)

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

    def get_day_offs(self):

        return self.repository.get_all()

    def is_day_off(
        self,
        value,
    ):

        value = self.normalize_date(value)

        return self.repository.exists(value)

    # ---------------- Create / Delete ---------------- #

    def add_day_off(
        self,
        value,
        reason=None,
    ):

        value = self.normalize_date(value)

        if self.repository.exists(value):

            raise ValueError(
                f"Clinic already has a day off on {value}."
            )

        return self.repository.create(
            {
                "date": value,
                "reason": reason,
            }
        )

    def remove_day_off(
        self,
        value,
    ):

        value = self.normalize_date(value)

        day_off = self.repository.get_by_date(value)

        return self.repository.delete(day_off)