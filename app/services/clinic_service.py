from app.database.models import Clinic
from app.repositories.clinic_repository import ClinicRepository


def get_current_clinic(db):
    """Return the single clinic record.

    This is the single point of truth for clinic resolution in a
    single-clinic architecture:

    - 0 clinics   -> raises ValueError (application error).
    - 1 clinic    -> returns it.
    - >1 clinics  -> raises ValueError (never silently picks one).

    Never use `.first()` here: that would hide duplicate clinic records.
    """
    clinics = db.query(Clinic).order_by(Clinic.id).all()

    if not clinics:

        raise ValueError(
            "No clinic record found. Run the clinic migration/seed first."
        )

    if len(clinics) > 1:

        raise ValueError(
            f"Expected exactly one clinic record but found {len(clinics)}. "
            "Run the single-clinic cleanup migration."
        )

    return clinics[0]


class ClinicService:

    def __init__(self, db):

        self.db = db

        self.repository = ClinicRepository(db)

    def get(self):

        return get_current_clinic(self.db)

    def get_active(self):

        return get_current_clinic(self.db)

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
