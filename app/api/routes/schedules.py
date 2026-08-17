from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.deps import get_db
from app.api.schemas.schedule import ScheduleDayResponse
from app.api.schemas.schedule import ScheduleUpdate
from app.services.doctor_schedule_service import DoctorScheduleService
from app.services.doctor_service import DoctorService

router = APIRouter(
    prefix="/api/doctors/{doctor_id}/schedule",
    tags=["schedules"],
    dependencies=[Depends(get_current_admin)],
)

WEEKDAYS = DoctorScheduleService.WEEKDAYS


def _get_or_404(db, doctor_id):

    doctor = DoctorService(db).get_by_id(doctor_id)

    if doctor is None:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )

    return doctor


def _to_response(schedule):

    return ScheduleDayResponse(
        weekday=schedule.day_of_week,
        weekday_name=WEEKDAYS[schedule.day_of_week],
        enabled=schedule.enabled,
        morning_start=schedule.morning_start,
        morning_end=schedule.morning_end,
        evening_start=schedule.evening_start,
        evening_end=schedule.evening_end,
    )


@router.get("", response_model=list[ScheduleDayResponse])
def get_doctor_schedule(
    doctor_id: int,
    db: Session = Depends(get_db),
):

    _get_or_404(db, doctor_id)

    schedules = DoctorScheduleService(db).get_doctor_schedule(doctor_id)

    return [
        _to_response(schedule)
        for schedule in schedules
    ]


@router.put("/{weekday}", response_model=ScheduleDayResponse)
def upsert_day_schedule(
    doctor_id: int,
    weekday: str,
    payload: ScheduleUpdate,
    db: Session = Depends(get_db),
):

    _get_or_404(db, doctor_id)

    try:

        schedule = DoctorScheduleService(db).save_day_schedule(
            doctor_id,
            weekday,
            payload.model_dump(exclude_unset=True),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return _to_response(schedule)
