from app.database.models import DoctorDayOff


class DoctorDayOffRepository:

    def __init__(self, db):

        self.db = db

    # ---------------- Queries ---------------- #

    def get_by_doctor(
        self,
        doctor_id,
    ):

        return (
            self.db.query(DoctorDayOff)
            .filter(
                DoctorDayOff.doctor_id == doctor_id,
            )
            .order_by(
                DoctorDayOff.date,
            )
            .all()
        )

    def get_by_doctor_and_date(
        self,
        doctor_id,
        date,
    ):

        return (
            self.db.query(DoctorDayOff)
            .filter(
                DoctorDayOff.doctor_id == doctor_id,
                DoctorDayOff.date == date,
            )
            .first()
        )

    def exists(
        self,
        doctor_id,
        date,
    ):

        return (
            self.db.query(DoctorDayOff)
            .filter(
                DoctorDayOff.doctor_id == doctor_id,
                DoctorDayOff.date == date,
            )
            .first()
        ) is not None

    # ---------------- Create / Delete ---------------- #

    def create(
        self,
        day_off_data: dict,
    ):

        day_off = DoctorDayOff(**day_off_data)

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

        return True