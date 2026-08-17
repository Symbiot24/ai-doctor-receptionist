from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.appointment import AppointmentResponse
from app.api.schemas.appointment import RescheduleInput
from app.api.schemas.appointment import StatusInput
from app.database.models import Appointment
from app.repositories.appointment_repository import AppointmentRepository
from app.services.slot_service import SlotService

router = APIRouter(
    prefix="/api/appointments",
    tags=["appointments"],
)


def _get_or_404(
    repository: AppointmentRepository,
    appointment_id: int,
):

    appointment = repository.get_by_id(appointment_id)

    if appointment is None:

        raise HTTPException(
            status_code=404,
            detail="Appointment not found.",
        )

    return appointment


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(
    status: Optional[str] = Query(None, description="Filter by status: BOOKED, COMPLETED, CANCELLED, NO_SHOW"),
    db: Session = Depends(get_db),
):

    query = db.query(Appointment)

    if status:

        query = query.filter(
            Appointment.status == status.strip().upper(),
        )

    return (
        query.order_by(
            Appointment.appointment_date,
            Appointment.appointment_time,
        )
        .all()
    )


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):

    repository = AppointmentRepository(db)

    appointment = _get_or_404(repository, appointment_id)

    if appointment.status == "CANCELLED":

        raise HTTPException(
            status_code=400,
            detail="Appointment is already cancelled.",
        )

    return repository.cancel(appointment)


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appointment_id: int,
    payload: RescheduleInput,
    db: Session = Depends(get_db),
):

    repository = AppointmentRepository(db)

    appointment = _get_or_404(repository, appointment_id)

    if appointment.status != "BOOKED":

        raise HTTPException(
            status_code=400,
            detail="Only booked appointments can be rescheduled.",
        )

    slot_service = SlotService(db)

    if not slot_service.is_slot_available(
        appointment.doctor,
        payload.appointment_date,
        payload.appointment_time,
        exclude_appointment_id=appointment_id,
    ):

        raise HTTPException(
            status_code=409,
            detail="That time slot is not available.",
        )

    return repository.reschedule(
        appointment,
        payload.appointment_date,
        payload.appointment_time,
    )


@router.post("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    payload: StatusInput,
    db: Session = Depends(get_db),
):

    repository = AppointmentRepository(db)

    appointment = _get_or_404(repository, appointment_id)

    if appointment.status == "CANCELLED":

        raise HTTPException(
            status_code=400,
            detail="A cancelled appointment cannot change status.",
        )

    appointment.status = payload.status

    db.commit()

    db.refresh(appointment)

    return appointment
