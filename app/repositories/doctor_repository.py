from sqlalchemy import or_

from app.database.models import Doctor


class DoctorRepository:

    def __init__(self, db):

        self.db = db

    # ---------------- Create ---------------- #

    def create(
        self,
        doctor_data: dict,
    ):

        doctor = Doctor(**doctor_data)

        self.db.add(doctor)

        self.db.commit()

        self.db.refresh(doctor)

        return doctor

    # ---------------- Update ---------------- #

    def update(
        self,
        doctor,
        updates: dict,
    ):

        for key, value in updates.items():

            setattr(doctor, key, value)

        self.db.commit()

        self.db.refresh(doctor)

        return doctor

    # ---------------- Active Status ---------------- #

    def activate(
        self,
        doctor,
    ):

        doctor.active = "YES"

        self.db.commit()

        self.db.refresh(doctor)

        return doctor

    def deactivate(
        self,
        doctor,
    ):

        doctor.active = "NO"

        self.db.commit()

        self.db.refresh(doctor)

        return doctor

    # ---------------- Queries ---------------- #

    def get_all(self):

        # Backward-compatible: Telegram booking and AI context
        # rely on this returning ONLY active doctors.
        return (
            self.db.query(Doctor)
            .filter(
                Doctor.active == "YES"
            )
            .all()
        )

    def get_active(self):

        return (
            self.db.query(Doctor)
            .filter(
                Doctor.active == "YES"
            )
            .all()
        )

    def get_all_including_inactive(self):

        # Admin-facing: the API needs the full roster so deactivated
        # doctors can be reactivated. Telegram/AI paths keep using
        # get_all() (active-only) for backward compatibility.
        return (
            self.db.query(Doctor)
            .order_by(
                Doctor.id,
            )
            .all()
        )

    def get_by_id(
        self,
        doctor_id,
    ):

        return (
            self.db.query(Doctor)
            .filter(
                Doctor.id == doctor_id,
            )
            .first()
        )

    def exists(self, name):

        return (
            self.db.query(Doctor)
            .filter(
                Doctor.name == name,
                Doctor.active == "YES",
            )
            .first()
        )

    def find_by_name(self, name):

        return (
            self.db.query(Doctor)
            .filter(
                Doctor.active == "YES",
                or_(
                    Doctor.name.ilike(f"%{name}%"),
                    Doctor.name.ilike(f"%{name.strip().title()}%"),
                ),
            )
            .first()
        )

    def search_by_name(self, name):

        return (
            self.db.query(Doctor)
            .filter(
                Doctor.active == "YES",
                Doctor.name.ilike(f"%{name}%"),
            )
            .all()
        )

    def get_by_specialty(self, specialty):

        return (
            self.db.query(Doctor)
            .filter(
                Doctor.active == "YES",
                Doctor.specialization.ilike(f"%{specialty}%"),
            )
            .all()
        )