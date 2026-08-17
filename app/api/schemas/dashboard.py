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


class DashboardSummary(BaseModel):
    total_active_doctors: int
    total_doctors: int
    today_appointments: int
    upcoming_appointments: int
    unavailable_doctors: int
    upcoming_list: list[DashboardAppointment]
