from datetime import date
from typing import List

from pydantic import BaseModel


class AvailabilityResponse(BaseModel):
    date: date
    doctor_id: int
    slots: List[str]
