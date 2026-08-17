from datetime import date

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.deps import get_db
from app.api.schemas.dashboard import DashboardSummary
from app.database.models import Appointment
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService

router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):

    doctor_service = DoctorService(db)

    slot_service = SlotService(db)

    all_doctors = doctor_service.get_all_including_inactive()

    active_doctors = [doctor for doctor in all_doctors if doctor.active == "YES"]

    today = date.today()

    booked = (
        db.query(Appointment)
        .filter(Appointment.status == "BOOKED")
        .order_by(
            Appointment.appointment_date,
            Appointment.appointment_time,
        )
        .all()
    )

    today_appointments = sum(
        1 for appointment in booked if appointment.appointment_date == today
    )

    upcoming = [appointment for appointment in booked if appointment.appointment_date >= today]

    # A doctor is "unavailable today" when no bookable slot can be generated
    # (inactive, day-off, disabled weekday, or no configured shifts).
    unavailable_doctors = sum(
        1
        for doctor in active_doctors
        if not slot_service.available_slots_for_id(doctor.id, today)
    )

    return DashboardSummary(
        total_active_doctors=len(active_doctors),
        total_doctors=len(all_doctors),
        today_appointments=today_appointments,
        upcoming_appointments=len(upcoming),
        unavailable_doctors=unavailable_doctors,
        upcoming_list=upcoming[:8],
    )
