from datetime import date
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.day_off import DayOffCreate
from app.api.schemas.day_off import DayOffResponse
from app.services.doctor_day_off_service import DoctorDayOffService
from app.services.doctor_service import DoctorService

router = APIRouter(
    prefix="/api/doctors/{doctor_id}/day-offs",
    tags=["day-offs"],
)


def _get_or_404(db, doctor_id):

    doctor = DoctorService(db).get_by_id(doctor_id)

    if doctor is None:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )

    return doctor


@router.get("", response_model=list[DayOffResponse])
def list_day_offs(
    doctor_id: int,
    db: Session = Depends(get_db),
):

    _get_or_404(db, doctor_id)

    return DoctorDayOffService(db).get_day_offs(doctor_id)


@router.post("", response_model=DayOffResponse, status_code=201)
def add_day_off(
    doctor_id: int,
    payload: DayOffCreate,
    db: Session = Depends(get_db),
):

    _get_or_404(db, doctor_id)

    try:

        return DoctorDayOffService(db).add_day_off(
            doctor_id,
            payload.date,
            payload.reason,
        )

    except ValueError as error:

        message = str(error)

        if "already has a day off" in message:

            raise HTTPException(
                status_code=409,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )


@router.delete("/{day_off_date}", status_code=204)
def remove_day_off(
    doctor_id: int,
    day_off_date: date,
    db: Session = Depends(get_db),
):

    _get_or_404(db, doctor_id)

    removed = DoctorDayOffService(db).remove_day_off(
        doctor_id,
        day_off_date,
    )

    if removed is None:

        raise HTTPException(
            status_code=404,
            detail="Day-off not found.",
        )

    return Response(status_code=204)
