from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Date
from sqlalchemy import Time
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy import UniqueConstraint
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

    status = Column(
        String,
        default="BOOKED",
        nullable=False,
    )

    clinic_id = Column(
        Integer,
        nullable=False,
    )

    reminder_24h_sent = Column(
        Boolean,
        default=False,
    )

    reminder_1h_sent = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class Clinic(Base):

    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True)

    name = Column(String(100), nullable=False)

    description = Column(Text)

    phone = Column(String(20))

    address = Column(String(255))

    active = Column(
        String,
        default="YES",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

class Doctor(Base):

    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)

    name = Column(String(100), nullable=False)

    specialization = Column(String(100))

    consultation_fee = Column(Integer)

    morning_start = Column(Time)

    morning_end = Column(Time)

    evening_start = Column(Time)

    evening_end = Column(Time)

    active = Column(
        String,
        default="YES",
    )

    clinic_id = Column(
        Integer,
        nullable=False,
    )

    # ---------------- Compatibility Alias ---------------- #

    @property
    def start_time(self):
        return self.morning_start

    @property
    def end_time(self):
        return self.evening_end

    @property
    def working_hours(self):
        """Human-readable split shift timings.

        Returns e.g. "10:00 - 14:00, 16:00 - 19:00"
        or "" when no shifts are configured.
        """
        shifts = []
        if self.morning_start and self.morning_end:
            shifts.append(
                f"{self.morning_start.strftime('%H:%M')} - "
                f"{self.morning_end.strftime('%H:%M')}"
            )
        if self.evening_start and self.evening_end:
            shifts.append(
                f"{self.evening_start.strftime('%H:%M')} - "
                f"{self.evening_end.strftime('%H:%M')}"
            )
        return ", ".join(shifts) if shifts else ""


class DoctorDayOff(Base):

    __tablename__ = "doctor_day_offs"

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "date",
            name="uq_doctor_day_off",
        ),
    )

    id = Column(Integer, primary_key=True)

    doctor_id = Column(Integer, nullable=False)

    date = Column(Date, nullable=False)

    reason = Column(String(255))


class DoctorSchedule(Base):

    __tablename__ = "doctor_schedules"

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "day_of_week",
            name="uq_doctor_schedule_day",
        ),
    )

    id = Column(Integer, primary_key=True)

    doctor_id = Column(Integer, nullable=False)

    day_of_week = Column(Integer, nullable=False)

    enabled = Column(
        Boolean,
        default=True,
    )

    morning_start = Column(Time)

    morning_end = Column(Time)

    evening_start = Column(Time)

    evening_end = Column(Time)