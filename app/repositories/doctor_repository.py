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