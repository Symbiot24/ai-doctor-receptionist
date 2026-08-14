from app.database.models import Clinic


class ClinicRepository:

    def __init__(self, db):

        self.db = db

    def get(self):

        return self.db.query(Clinic).first()

    def get_active(self):

        return (
            self.db.query(Clinic)
            .filter(
                Clinic.active == "YES"
            )
            .first()
        )

    def create(
        self,
        clinic_data: dict,
    ):

        clinic = Clinic(**clinic_data)

        self.db.add(clinic)

        self.db.commit()

        self.db.refresh(clinic)

        return clinic

    def update(
        self,
        clinic,
        updates: dict,
    ):

        for key, value in updates.items():

            setattr(clinic, key, value)

        self.db.commit()

        self.db.refresh(clinic)

        return clinic