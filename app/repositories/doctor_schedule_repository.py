from app.database.models import DoctorSchedule


class DoctorScheduleRepository:

    def __init__(self, db):

        self.db = db

    # ---------------- Queries ---------------- #

    def get_by_doctor(
        self,
        doctor_id,
    ):

        return (
            self.db.query(DoctorSchedule)
            .filter(
                DoctorSchedule.doctor_id == doctor_id,
            )
            .order_by(
                DoctorSchedule.day_of_week,
            )
            .all()
        )

    def get_by_doctor_and_day(
        self,
        doctor_id,
        day_of_week,
    ):

        return (
            self.db.query(DoctorSchedule)
            .filter(
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.day_of_week == day_of_week,
            )
            .first()
        )

    # ---------------- Create / Update / Delete ---------------- #

    def create(
        self,
        schedule_data: dict,
    ):

        schedule = DoctorSchedule(**schedule_data)

        self.db.add(schedule)

        self.db.commit()

        self.db.refresh(schedule)

        return schedule

    def update(
        self,
        schedule,
        updates: dict,
    ):

        for key, value in updates.items():

            setattr(schedule, key, value)

        self.db.commit()

        self.db.refresh(schedule)

        return schedule

    def delete(
        self,
        schedule,
    ):

        if schedule is None:

            return None

        self.db.delete(schedule)

        self.db.commit()

        return True