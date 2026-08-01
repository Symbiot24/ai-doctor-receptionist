from datetime import date
from datetime import time

from pydantic import BaseModel
from pydantic import Field


class AppointmentSchema(BaseModel):

    patient_name: str = Field(...)

    phone: str = Field(...)

    age: int = Field(...)

    gender: str = Field(...)

    symptoms: str = Field(...)

    doctor: str = Field(...)

    appointment_date: date

    appointment_time: time