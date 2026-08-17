from datetime import date as date_type
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.availability import AvailabilityResponse
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService

router = APIRouter(
    prefix="/api/doctors/{doctor_id}/availability",
    tags=["availability"],
)


@router.get("", response_model=AvailabilityResponse)
def get_availability(
    doctor_id: int,
    date: date_type = Query(..., description="Date as YYYY-MM-DD"),
    db: Session = Depends(get_db),
):

    doctor = DoctorService(db).get_by_id(doctor_id)

    if doctor is None:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )

    slots = SlotService(db).available_slots_for_id(
        doctor_id,
        date,
    )

    return AvailabilityResponse(
        date=date,
        doctor_id=doctor_id,
        slots=slots,
    )
