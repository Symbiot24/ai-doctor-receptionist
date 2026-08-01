from app.repositories.doctor_repository import DoctorRepository


class DoctorService:

    def __init__(self, db):

        self.repository = DoctorRepository(db)

    def get_all(self):

        return self.repository.get_all()

    def exists(self, name):

        return self.repository.exists(name)