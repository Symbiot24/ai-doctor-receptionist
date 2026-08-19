from datetime import date
from typing import List
from typing import Optional

from pydantic import BaseModel


class AvailabilityResponse(BaseModel):
    date: date
    doctor_id: int
    slots: List[str]
    available: bool
    reason: Optional[str] = None
