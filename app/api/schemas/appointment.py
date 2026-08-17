from datetime import date
from datetime import datetime
from datetime import time
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_serializer


class AppointmentResponse(BaseModel):
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


class RescheduleInput(BaseModel):
    appointment_date: date
    appointment_time: time


class StatusInput(BaseModel):
    status: Literal["COMPLETED", "NO_SHOW"]
