from sqlalchemy import or_

from app.database.models import Doctor


class DoctorRepository:

    def __init__(self, db):

        self.db = db

    def get_all(self):

        return (
            self.db.query(Doctor)
            .filter(
                Doctor.active == "YES"
            )
            .all()
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