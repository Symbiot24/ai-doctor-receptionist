from datetime import datetime

from app.database.models import Clinic
from app.repositories.doctor_repository import DoctorRepository
from app.services.doctor_validator import DoctorValidator


class DoctorService:

    TIME_FIELDS = (
        "morning_start",
        "morning_end",
        "evening_start",
        "evening_end",
    )

    def __init__(self, db):

        self.db = db

        self.repository = DoctorRepository(db)

    # ---------------- Normalization ---------------- #

    def _normalize(
        self,
        data: dict,
    ):

        for field in self.TIME_FIELDS:

            value = data.get(field)

            if isinstance(value, str):

                data[field] = datetime.strptime(value, "%H:%M").time()

        if "consultation_fee" in data and data.get("consultation_fee") is not None:

            data["consultation_fee"] = int(data["consultation_fee"])

        return data

    # ---------------- Clinic Association ---------------- #

    def _default_clinic_id(self):

        clinic = (
            self.db.query(Clinic)
            .filter(
                Clinic.active == "YES"
            )
            .first()
        )

        if clinic is None:

            clinic = self.db.query(Clinic).first()

        if clinic is None:

            raise ValueError(
                "No clinic record found. Run the clinic migration/seed first."
            )

        return clinic.id

    # ---------------- Create ---------------- #

    def create(
        self,
        doctor_data: dict,
    ):

        doctor_data = dict(doctor_data)

        # Single-clinic system: auto-associate with the existing clinic.
        # Never trust a clinic_id supplied by the caller.
        doctor_data.pop("clinic_id", None)

        doctor_data["clinic_id"] = self._default_clinic_id()

        doctor_data = self._normalize(doctor_data)

        errors = DoctorValidator.validate(doctor_data)

        if errors:

            raise ValueError("; ".join(errors))

        return self.repository.create(doctor_data)

    # ---------------- Update ---------------- #

    def update(
        self,
        doctor_id,
        updates: dict,
    ):

        doctor = self.repository.get_by_id(doctor_id)

        if doctor is None:

            return None

        updates = dict(updates)

        # Clinic association is managed by the backend only.
        updates.pop("clinic_id", None)

        updates = self._normalize(updates)

        errors = DoctorValidator.validate(updates, partial=True)

        if errors:

            raise ValueError("; ".join(errors))

        return self.repository.update(doctor, updates)

    # ---------------- Active Status ---------------- #

    def activate(
        self,
        doctor_id,
    ):

        doctor = self.repository.get_by_id(doctor_id)

        if doctor is None:

            return None

        return self.repository.activate(doctor)

    def deactivate(
        self,
        doctor_id,
    ):

        doctor = self.repository.get_by_id(doctor_id)

        if doctor is None:

            return None

        return self.repository.deactivate(doctor)

    # ---------------- Queries ---------------- #

    def get_all(self):

        return self.repository.get_all()

    def get_active(self):

        return self.repository.get_active()

    def get_by_id(
        self,
        doctor_id,
    ):

        return self.repository.get_by_id(doctor_id)

    def exists(self, name):

        return self.repository.exists(name)

    def find_by_name(self, name):

        return self.repository.find_by_name(name)

    def search_by_name(self, name):

        return self.repository.search_by_name(name)

    def get_by_specialty(self, specialty):

        return self.repository.get_by_specialty(specialty)