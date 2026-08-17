from datetime import date
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict


class DayOffCreate(BaseModel):
    date: date
    reason: Optional[str] = None


class DayOffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    reason: Optional[str] = None
