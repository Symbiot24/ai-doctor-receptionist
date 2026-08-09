from app.repositories.doctor_repository import DoctorRepository


class DoctorService:

    def __init__(self, db):

        self.repository = DoctorRepository(db)

    def get_all(self):

        return self.repository.get_all()

    def exists(self, name):

        return self.repository.exists(name)

    def find_by_name(self, name):

        return self.repository.find_by_name(name)

    def search_by_name(self, name):

        return self.repository.search_by_name(name)

    def get_by_specialty(self, specialty):

        return self.repository.get_by_specialty(specialty)