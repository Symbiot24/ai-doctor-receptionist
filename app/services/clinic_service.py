from app.repositories.clinic_repository import ClinicRepository


class ClinicService:

    def __init__(self, db):

        self.repository = ClinicRepository(db)

    def get(self):

        return self.repository.get()

    def get_active(self):

        return self.repository.get_active()

    def create(
        self,
        clinic_data: dict,
    ):

        return self.repository.create(clinic_data)

    def update(
        self,
        clinic,
        updates: dict,
    ):

        return self.repository.update(clinic, updates)