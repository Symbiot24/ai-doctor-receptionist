from datetime import date
from datetime import datetime
from datetime import time
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_serializer


class DashboardAppointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_name: Optional[str] = None
    telegram_id: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    symptoms: Optional[str] = None
    doctor: Optional[str] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    status: str
    created_at: Optional[datetime] = None

    @field_serializer("appointment_time")
    def _serialize_time(self, value: Optional[time]):
        return value.strftime("%H:%M") if value else None


class DoctorAvailability(BaseModel):
    """Per-doctor availability snapshot so the dashboard can explain WHY a
    doctor is or is not bookable today instead of showing contradictory
    counts.

    ``status`` is one of:
    - "available"   -> active and has bookable slots today
    - "unavailable" -> active but off today (day-off or disabled weekday)
    - "inactive"    -> deactivated in the system
    """

    id: int
    name: str
    specialization: Optional[str] = None
    active: str
    is_active: Optional[str] = None
    available_today: bool
    status: str
    reason: Optional[str] = None


class DashboardSummary(BaseModel):
    total_active_doctors: int
    total_doctors: int
    unavailable_doctors: int
    inactive_doctors: int
    today_appointments: int
    upcoming_appointments: int
    doctor_availability: list[DoctorAvailability]
    upcoming_list: list[DashboardAppointment]