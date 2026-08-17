from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.doctor import DoctorCreate
from app.api.schemas.doctor import DoctorResponse
from app.api.schemas.doctor import DoctorUpdate
from app.services.doctor_service import DoctorService

router = APIRouter(
    prefix="/api/doctors",
    tags=["doctors"],
)


def _get_or_404(db, doctor_id):

    doctor = DoctorService(db).get_by_id(doctor_id)

    if doctor is None:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )

    return doctor


@router.get("", response_model=list[DoctorResponse])
def list_doctors(db: Session = Depends(get_db)):

    # Admin-facing full roster (includes deactivated doctors so the
    # frontend can reactivate them).
    return DoctorService(db).get_all_including_inactive()


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
):

    return _get_or_404(db, doctor_id)


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
