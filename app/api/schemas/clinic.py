from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class ClinicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    active: Optional[str] = None
