"""Focused tests for doctor-specific date-based day-offs.

Runnable standalone (project has no pytest setup):

    python -m tests.test_doctor_day_off

Creates a uniquely-named test doctor against the real database, verifies
the day-off repository/service and slot-service integration, and cleans up
all test rows afterwards.
"""

import sys
import time
from datetime import date
from datetime import datetime
from datetime import timedelta

from app.database.db import SessionLocal
from app.database.migrations import ensure_doctor_day_off_table
from app.database.models import Doctor
from app.database.models import DoctorDayOff
from app.database.models import DoctorSchedule
from app.services.doctor_service import DoctorService
from app.services.doctor_schedule_service import DoctorScheduleService
from app.services.doctor_day_off_service import DoctorDayOffService
from app.services.slot_service import SlotService
from app.services.appointment_service import AppointmentService

PASSED = []
FAILED = []


def check(label, condition, detail=""):
    if condition:
        PASSED.append(label)
        print(f"  PASS  {label} {detail}")
    else:
        FAILED.append(label)
        print(f"  FAIL  {label} {detail}")


def next_date_with_weekday(day_of_week):
    day = date.today() + timedelta(days=7)
    while day.weekday() != day_of_week:
        day += timedelta(days=1)
    return day


def main():

    ensure_doctor_day_off_table()

    db = SessionLocal()

    suffix = str(int(time.time()))

    doctor_name = f"Dr Off {suffix}"

    doctor_id = None

    try:

        doctor_service = DoctorService(db)

        schedule_service = DoctorScheduleService(db)

        day_off_service = DoctorDayOffService(db)

        slot_service = SlotService(db)

        print("== SETUP: TEST DOCTOR ==")

        doctor = doctor_service.create(
            {
                "name": doctor_name,
                "specialization": "Day Off Test",
                "consultation_fee": 450,
            }
        )

        doctor_id = doctor.id

        schedule_service.save_day_schedule(
            doctor_id,
            0,
            {
                "enabled": True,
                "morning_start": "10:00",
                "morning_end": "14:00",
                "evening_start": "16:00",
                "evening_end": "19:00",
            },
        )

        schedule_service.save_day_schedule(
            doctor_id,
            2,
            {
                "enabled": False,
                "morning_start": "10:00",
                "morning_end": "14:00",
            },
        )

        monday_date = next_date_with_weekday(0)

        wednesday_date = next_date_with_weekday(2)

        print("== ADD / RETRIEVE DAY-OFF ==")

        day_off = day_off_service.add_day_off(
            doctor_id,
            monday_date,
            reason="Personal leave",
        )

        check(
            "add day-off",
            day_off is not None
            and day_off.doctor_id == doctor_id
            and day_off.date == monday_date,
            f"(id={day_off.id})",
        )

        retrieved = day_off_service.get_day_offs(doctor_id)

        check(
            "retrieve day-offs",
            any(o.date == monday_date for o in retrieved),
            f"(count={len(retrieved)})",
        )

        check(
            "is_day_off true",
            day_off_service.is_day_off(doctor_id, monday_date) is True,
        )

        print("== DUPLICATE REJECTION ==")

        try:
            day_off_service.add_day_off(doctor_id, monday_date)
            check("duplicate day-off rejection", False, "should have raised")
        except ValueError as error:
            check(
                "duplicate day-off rejection",
                "already has a day off" in str(error),
                str(error),
            )

        print("== NONEXISTENT DOCTOR HANDLING ==")

        try:
            day_off_service.add_day_off(999999, monday_date)
            check("nonexistent doctor add", False, "should have raised")
        except ValueError as error:
            check(
                "nonexistent doctor add",
                "not found" in str(error),
                str(error),
            )

        check(
            "nonexistent doctor is_day_off safe",
            day_off_service.is_day_off(999999, monday_date) is False,
        )

        check(
            "nonexistent doctor remove safe",
            day_off_service.remove_day_off(999999, monday_date) is None,
        )

        print("== INVALID DATE ==")

        try:
            day_off_service.add_day_off(doctor_id, "not-a-date")
            check("invalid date", False, "should have raised")
        except ValueError as error:
            check(
                "invalid date",
                "YYYY-MM-DD" in str(error),
                str(error),
            )

        print("== SLOT AVAILABILITY ==")

        print("  -- working day without day-off --")

        other_monday = monday_date + timedelta(days=7)

        working_slots = slot_service.available_slots(doctor_name, other_monday)

        check(
            "weekly working day has slots",
            len(working_slots) > 0,
            f"({len(working_slots)} slots)",
        )

        print("  -- working day WITH day-off --")

        off_slots = slot_service.available_slots(doctor_name, monday_date)

        check(
            "day-off overrides working schedule",
            off_slots == [],
        )

        print("  -- weekly OFF day --")

        wednesday_slots = slot_service.available_slots(doctor_name, wednesday_date)

        check(
            "weekly off day has no slots",
            wednesday_slots == [],
        )

        print("== BOOKED SLOTS STILL EXCLUDED ==")

        book_service = AppointmentService(db)

        book_service.book(
            {
                "patient_name": "Off Booked",
                "telegram_id": f"off-{suffix}",
                "doctor": doctor_name,
                "appointment_date": other_monday,
                "appointment_time": datetime.strptime("10:00", "%H:%M").time(),
            }
        )

        slots_after = slot_service.available_slots(doctor_name, other_monday)

        check(
            "booked slot excluded on working day",
            "10:00" not in slots_after and "10:30" in slots_after,
        )

        print("== REMOVE DAY-OFF ==")

        check(
            "remove day-off",
            day_off_service.remove_day_off(doctor_id, monday_date) is True,
        )

        check(
            "is_day_off false after removal",
            day_off_service.is_day_off(doctor_id, monday_date) is False,
        )

        check(
            "slots return after day-off removal",
            len(slot_service.available_slots(doctor_name, monday_date)) > 0,
        )

    finally:

        db.rollback()

        if doctor_id is not None:

            AppointmentModel = __import__(
                "app.database.models",
                fromlist=["Appointment"],
            ).Appointment

            for off in db.query(DoctorDayOff).filter(
                DoctorDayOff.doctor_id == doctor_id
            ).all():
                db.delete(off)

            for sched in db.query(DoctorSchedule).filter(
                DoctorSchedule.doctor_id == doctor_id
            ).all():
                db.delete(sched)

            for appt in db.query(AppointmentModel).filter(
                AppointmentModel.doctor == doctor_name
            ).all():
                db.delete(appt)

            db.commit()

            doc = db.get(Doctor, doctor_id)

            if doc is not None:
                db.delete(doc)
                db.commit()

        db.close()

    print()
    print(f"PASSED: {len(PASSED)}")
    print(f"FAILED: {len(FAILED)}")

    for label in FAILED:
        print(f"  - {label}")

    if FAILED:
        sys.exit(1)

    print("DOCTOR DAY-OFF TESTS OK")


if __name__ == "__main__":

    main()