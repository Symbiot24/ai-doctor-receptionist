from datetime import date

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.clinic_day_off import ClinicDayOffCreate
from app.api.schemas.clinic_day_off import ClinicDayOffResponse
from app.services.clinic_day_off_service import ClinicDayOffService

router = APIRouter(
    prefix="/api/clinic/day-offs",
    tags=["clinic-day-offs"],
)


@router.get("", response_model=list[ClinicDayOffResponse])
def list_day_offs(
    db: Session = Depends(get_db),
):

    return ClinicDayOffService(db).get_day_offs()


@router.post("", response_model=ClinicDayOffResponse, status_code=201)
def add_day_off(
    payload: ClinicDayOffCreate,
    db: Session = Depends(get_db),
):

    try:

        return ClinicDayOffService(db).add_day_off(
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
    day_off_date: date,
    db: Session = Depends(get_db),
):

    removed = ClinicDayOffService(db).remove_day_off(
        day_off_date,
    )

    if removed is None:

        raise HTTPException(
            status_code=404,
            detail="Clinic day-off not found.",
        )

    return Response(status_code=204)