from app.database.models import ClinicDayOff


class ClinicDayOffRepository:

    def __init__(self, db):

        self.db = db

    # ---------------- Queries ---------------- #

    def get_all(self):

        return (
            self.db.query(ClinicDayOff)
            .order_by(ClinicDayOff.date)
            .all()
        )

    def get_by_date(
        self,
        date,
    ):

        return (
            self.db.query(ClinicDayOff)
            .filter(
                ClinicDayOff.date == date,
            )
            .first()
        )

    def exists(
        self,
        date,
    ):

        return self.get_by_date(date) is not None

    # ---------------- Create / Delete ---------------- #

    def create(
        self,
        day_off_data: dict,
    ):

        day_off = ClinicDayOff(**day_off_data)

        self.db.add(day_off)

        self.db.commit()

        self.db.refresh(day_off)

        return day_off

    def delete(
        self,
        day_off,
    ):

        if day_off is None:

            return None

        self.db.delete(day_off)

        self.db.commit()

        return day_off