from datetime import time
from typing import Optional

from pydantic import BaseModel
from pydantic import field_serializer


class ScheduleUpdate(BaseModel):
    enabled: Optional[bool] = True
    morning_start: Optional[time] = None
    morning_end: Optional[time] = None
    evening_start: Optional[time] = None
    evening_end: Optional[time] = None


class ScheduleDayResponse(BaseModel):
    weekday: int
    weekday_name: str
    enabled: bool
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
