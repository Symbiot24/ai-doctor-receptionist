from datetime import date as date_type
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.deps import get_db
from app.api.schemas.availability import AvailabilityResponse
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService

router = APIRouter(
    prefix="/api/doctors/{doctor_id}/availability",
    tags=["availability"],
    dependencies=[Depends(get_current_admin)],
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

    slot_service = SlotService(db)

    available, reason = slot_service.availability_status(
        doctor,
        date,
    )

    return AvailabilityResponse(
        date=date,
        doctor_id=doctor_id,
        slots=slot_service.available_slots_for_id(
            doctor_id,
            date,
        ),
        available=available,
        reason=reason,
    )
