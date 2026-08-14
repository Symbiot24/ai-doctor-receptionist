"""Focused tests for the weekly doctor schedule system.

Runnable standalone (project has no pytest setup):

    python -m tests.test_doctor_schedule

Creates a uniquely-named test doctor against the real database, verifies
the schedule repository/service/slot integration, and cleans up all test
rows afterwards.
"""

import sys
import time
from datetime import date
from datetime import datetime
from datetime import timedelta

from app.database.db import SessionLocal
from app.database.migrations import ensure_doctor_schedule_table
from app.services.doctor_service import DoctorService
from app.services.doctor_schedule_service import DoctorScheduleService
from app.services.slot_service import SlotService
from app.services.appointment_service import AppointmentService
from app.database.models import Doctor
from app.database.models import DoctorSchedule

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

    ensure_doctor_schedule_table()

    db = SessionLocal()

    suffix = str(int(time.time()))

    doctor_name = f"Dr Sched {suffix}"

    doctor_id = None

    try:

        doctor_service = DoctorService(db)

        schedule_service = DoctorScheduleService(db)

        slot_service = SlotService(db)

        print("== SETUP: TEST DOCTOR ==")

        doctor = doctor_service.create(
            {
                "name": doctor_name,
                "specialization": "Scheduler Test",
                "consultation_fee": 400,
            }
        )

        doctor_id = doctor.id

        print("== MONDAY / TUESDAY SCHEDULE ==")

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
            "Tuesday",
            {
                "enabled": True,
                "morning_start": "10:00",
                "morning_end": "14:00",
                "evening_start": "16:00",
                "evening_end": "19:00",
            },
        )

        monday = schedule_service.get_day_schedule(doctor_id, 0)

        check(
            "monday schedule saved",
            monday is not None
            and monday.morning_start.strftime("%H:%M") == "10:00"
            and monday.evening_end.strftime("%H:%M") == "19:00",
            f"(id={monday.id if monday else None})",
        )

        tuesday = schedule_service.get_day_schedule(doctor_id, 1)

        check(
            "tuesday schedule by name",
            tuesday is not None and tuesday.day_of_week == 1,
        )

        print("== DISABLED DAY ==")

        schedule_service.save_day_schedule(
            doctor_id,
            2,
            {
                "enabled": False,
                "morning_start": "10:00",
                "morning_end": "14:00",
            },
        )

        wednesday = schedule_service.get_day_schedule(doctor_id, 2)

        check(
            "disabled day",
            wednesday is not None and wednesday.enabled is False,
        )

        print("== MORNING-ONLY SCHEDULE ==")

        schedule_service.save_day_schedule(
            doctor_id,
            3,
            {
                "enabled": True,
                "morning_start": "10:00",
                "morning_end": "13:00",
            },
        )

        thursday = schedule_service.get_day_schedule(doctor_id, 3)

        check(
            "morning-only schedule",
            thursday is not None
            and thursday.morning_start is not None
            and thursday.evening_start is None,
        )

        print("== EVENING-ONLY SCHEDULE ==")

        schedule_service.save_day_schedule(
            doctor_id,
            4,
            {
                "enabled": True,
                "evening_start": "17:00",
                "evening_end": "20:00",
            },
        )

        friday = schedule_service.get_day_schedule(doctor_id, 4)

        check(
            "evening-only schedule",
            friday is not None
            and friday.evening_start is not None
            and friday.morning_start is None,
        )

        print("== MORNING + EVENING SCHEDULE (UPSERT) ==")

        schedule_service.save_day_schedule(
            doctor_id,
            0,
            {
                "morning_start": "10:00",
                "morning_end": "14:00",
                "evening_start": "16:00",
                "evening_end": "19:00",
            },
        )

        monday_rows = [
            s for s in schedule_service.get_doctor_schedule(doctor_id)
            if s.day_of_week == 0
        ]

        check(
            "duplicate doctor+weekday upserts (no dup)",
            len(monday_rows) == 1,
            f"(rows={len(monday_rows)})",
        )

        schedule_service.save_day_schedule(
            doctor_id,
            5,
            {
                "enabled": True,
                "morning_start": "10:00",
                "morning_end": "14:00",
                "evening_start": "16:00",
                "evening_end": "19:00",
            },
        )

        full = schedule_service.get_doctor_schedule(doctor_id)

        check(
            "get_doctor_schedule lists weekdays",
            len(full) == 6 and sorted(s.day_of_week for s in full) == [0, 1, 2, 3, 4, 5],
            f"(count={len(full)})",
        )

        print("== VALIDATION ==")

        try:
            schedule_service.save_day_schedule(
                doctor_id,
                6,
                {"morning_start": "14:00", "morning_end": "10:00"},
            )
            check("invalid morning range", False, "should have raised")
        except ValueError as error:
            check(
                "invalid morning range",
                "end must be after start" in str(error),
                str(error),
            )

        try:
            schedule_service.save_day_schedule(
                doctor_id,
                6,
                {"evening_start": "19:00", "evening_end": "17:00"},
            )
            check("invalid evening range", False, "should have raised")
        except ValueError as error:
            check(
                "invalid evening range",
                "end must be after start" in str(error),
                str(error),
            )

        try:
            schedule_service.save_day_schedule(
                doctor_id,
                6,
                {
                    "morning_start": "10:00",
                    "morning_end": "14:00",
                    "evening_start": "13:00",
                    "evening_end": "16:00",
                },
            )
            check("overlapping shifts", False, "should have raised")
        except ValueError as error:
            check(
                "overlapping shifts",
                "must not overlap" in str(error),
                str(error),
            )

        try:
            schedule_service.save_day_schedule(
                doctor_id,
                99,
                {"enabled": True},
            )
            check("invalid weekday", False, "should have raised")
        except ValueError as error:
            check(
                "invalid weekday",
                "between 0 and 6" in str(error),
                str(error),
            )

        print("== SLOT GENERATION FROM WEEKLY SCHEDULE ==")

        monday_date = next_date_with_weekday(0)

        slots = slot_service.available_slots(doctor_name, monday_date)

        expected = (
            ["10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
             "13:00", "13:30",
             "16:00", "16:30", "17:00", "17:30", "18:00", "18:30"]
        )

        check(
            "monday slots within shifts",
            slots == expected,
            f"({len(slots)} slots)",
        )

        for gap in ("14:00", "14:30", "15:00", "15:30"):
            check(
                f"gap slot {gap} excluded",
                gap not in slots,
            )

        wednesday_date = next_date_with_weekday(2)

        wednesday_slots = slot_service.available_slots(doctor_name, wednesday_date)

        check(
            "disabled weekday returns no slots",
            wednesday_slots == [],
        )

        print("== BOOKED SLOTS STILL EXCLUDED ==")

        book_service = AppointmentService(db)

        appointment = book_service.book(
            {
                "patient_name": "Sched Booked",
                "telegram_id": f"sched-{suffix}",
                "doctor": doctor_name,
                "appointment_date": monday_date,
                "appointment_time": datetime.strptime("10:00", "%H:%M").time(),
            }
        )

        slots_after = slot_service.available_slots(doctor_name, monday_date)

        check(
            "booked slot excluded",
            "10:00" not in slots_after and "10:30" in slots_after,
        )

        print("== DELETE DAY ==")

        check(
            "delete day schedule",
            schedule_service.delete_day_schedule(doctor_id, 5) is True,
        )

        check(
            "day removed after delete",
            schedule_service.get_day_schedule(doctor_id, 5) is None,
        )

    finally:

        db.rollback()

        if doctor_id is not None:

            AppointmentModel = __import__(
                "app.database.models",
                fromlist=["Appointment"],
            ).Appointment

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

    print("DOCTOR SCHEDULE TESTS OK")


if __name__ == "__main__":

    main()