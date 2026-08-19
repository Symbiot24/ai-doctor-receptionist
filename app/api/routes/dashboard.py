from datetime import date

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.deps import get_db
from app.api.schemas.dashboard import DashboardSummary
from app.api.schemas.dashboard import DoctorAvailability
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

    active_doctors = [
        doctor for doctor in all_doctors if doctor.active == "YES"
    ]

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

    upcoming = [
        appointment
        for appointment in booked
        if appointment.appointment_date >= today
    ]

    # Build an explicit per-doctor breakdown so the numbers always add up:
    # total_active_doctors + unavailable_doctors + inactive_doctors
    # == total_doctors. A doctor who is active in the system but off today
    # (day-off or disabled weekday) counts as unavailable, not active.
    doctor_availability = []

    active_doctors_today = 0

    unavailable_doctors = 0

    for doctor in all_doctors:

        available, reason = slot_service.availability_status(
            doctor,
            today,
        )

        is_active = doctor.active == "YES"

        if not is_active:

            status = "inactive"

        elif available:

            status = "available"

        else:

            status = "unavailable"

        doctor_availability.append(
            DoctorAvailability(
                id=doctor.id,
                name=doctor.name,
                specialization=doctor.specialization,
                active="YES" if (is_active and available) else "NO",
                is_active=doctor.active,
                available_today=available,
                status=status,
                reason=reason,
            )
        )

        if is_active:

            if available:
                active_doctors_today += 1
            else:
                unavailable_doctors += 1

    inactive_doctors = len(all_doctors) - len(active_doctors)

    return DashboardSummary(
        total_active_doctors=active_doctors_today,
        total_doctors=len(all_doctors),
        unavailable_doctors=unavailable_doctors,
        inactive_doctors=inactive_doctors,
        today_appointments=today_appointments,
        upcoming_appointments=len(upcoming),
        doctor_availability=doctor_availability,
        upcoming_list=upcoming[:8],
    )