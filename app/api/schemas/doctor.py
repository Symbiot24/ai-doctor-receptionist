from datetime import time
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_serializer


class DoctorCreate(BaseModel):
    name: str
    specialization: str
    consultation_fee: Optional[int] = None
    active: Optional[str] = "YES"
    morning_start: Optional[time] = None
    morning_end: Optional[time] = None
    evening_start: Optional[time] = None
    evening_end: Optional[time] = None


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    consultation_fee: Optional[int] = None
    active: Optional[str] = None
    morning_start: Optional[time] = None
    morning_end: Optional[time] = None
    evening_start: Optional[time] = None
    evening_end: Optional[time] = None


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    specialization: Optional[str] = None
    consultation_fee: Optional[int] = None
    active: Optional[str] = None
    morning_start: Optional[time] = None
    morning_end: Optional[time] = None
    evening_start: Optional[time] = None
    evening_end: Optional[time] = None

    @field_serializer(
        "morning_start",
        "morning_end",
        "evening_start",
        "evening_end",
    )
    def _serialize_time(self, value: Optional[time]):
        return value.strftime("%H:%M") if value else None
