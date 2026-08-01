from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Date
from sqlalchemy import Time
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.database.db import Base


class Appointment(Base):

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)

    patient_name = Column(String(100))

    telegram_id = Column(String(50))

    phone = Column(String(20))

    age = Column(Integer)

    gender = Column(String(20))

    symptoms = Column(Text)

    doctor = Column(String(100))

    appointment_date = Column(Date)

    appointment_time = Column(Time)

    status = Column(String(20), default="Booked")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )