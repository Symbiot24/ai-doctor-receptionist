from datetime import date

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.deps import get_db
from app.api.schemas.doctor import DoctorCreate
from app.api.schemas.doctor import DoctorResponse
from app.api.schemas.doctor import DoctorUpdate
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService

router = APIRouter(
    prefix="/api/doctors",
    tags=["doctors"],
    dependencies=[Depends(get_current_admin)],
)


def _get_or_404(db, doctor_id):

    doctor = DoctorService(db).get_by_id(doctor_id)

    if doctor is None:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )

    return doctor


def _with_availability(doctor, slot_service):
    """Attach today's availability to a DoctorResponse.

    ``active`` reflects availability for today: a doctor who is active in
    the system but off today (day-off or disabled weekday) is reported as
    inactive for the day. ``is_active`` keeps the raw system status.
    """
    available_today, reason = slot_service.availability_status(
        doctor,
        date.today(),
    )

    is_active = doctor.active == "YES"

    response = DoctorResponse.model_validate(doctor)

    response.is_active = doctor.active

    response.available_today = available_today

    response.unavailable_reason = reason

    response.active = "YES" if (is_active and available_today) else "NO"

    return response


@router.get("", response_model=list[DoctorResponse])
def list_doctors(db: Session = Depends(get_db)):

    # Admin-facing full roster (includes deactivated doctors so the
    # frontend can reactivate them).
    doctor_service = DoctorService(db)

    slot_service = SlotService(db)

    doctors = doctor_service.get_all_including_inactive()

    return [
        _with_availability(doctor, slot_service)
        for doctor in doctors
    ]


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
):

    doctor = _get_or_404(db, doctor_id)

    return _with_availability(
        doctor,
        SlotService(db),
    )


@router.post("", response_model=DoctorResponse, status_code=201)
def create_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
):

    try:

        return DoctorService(db).create(
            payload.model_dump(exclude_unset=True)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
):

    _get_or_404(db, doctor_id)

    try:

        return DoctorService(db).update(
            doctor_id,
            payload.model_dump(exclude_unset=True),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.patch("/{doctor_id}/activate", response_model=DoctorResponse)
def activate_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
):

    doctor = DoctorService(db).activate(doctor_id)

    if doctor is None:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )

    return doctor


@router.patch("/{doctor_id}/deactivate", response_model=DoctorResponse)
def deactivate_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
):

    doctor = DoctorService(db).deactivate(doctor_id)

    if doctor is None:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )

    return doctor
