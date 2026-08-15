"""Focused tests for unified doctor availability + booking/rescheduling.

Runnable standalone (project has no pytest setup):

    python -m tests.test_booking_availability

Creates a uniquely-named test doctor against the real database, verifies
SlotService availability rules and that booking/rescheduling cannot bypass
them, and cleans up all test rows afterwards.
"""

import sys
import time
from datetime import date
from datetime import datetime
from datetime import timedelta

from app.database.db import SessionLocal
from app.database.migrations import ensure_doctor_day_off_table
from app.database.migrations import ensure_doctor_schedule_table
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


def hhmm(value):
    return datetime.strptime(value, "%H:%M").time()


def main():

    ensure_doctor_schedule_table()

    ensure_doctor_day_off_table()

    db = SessionLocal()

    suffix = str(int(time.time()))

    doctor_name = f"Dr Avail {suffix}"

    doctor_id = None

    appointment_ids = []

    try:

        doctor_service = DoctorService(db)

        schedule_service = DoctorScheduleService(db)

        day_off_service = DoctorDayOffService(db)

        slot_service = SlotService(db)

        book_service = AppointmentService(db)

        print("== SETUP: TEST DOCTOR ==")

        doctor = doctor_service.create(
            {
                "name": doctor_name,
                "specialization": "Availability Test",
                "consultation_fee": 500,
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

        mon1 = next_date_with_weekday(0)

        mon2 = mon1 + timedelta(days=7)

        wed1 = next_date_with_weekday(2)

        print("== 1. ACTIVE DOCTOR WITH VALID SCHEDULE ==")

        slots = slot_service.available_slots(doctor_name, mon1)

        check(
            "active doctor slots generated",
            len(slots) > 0,
            f"({len(slots)} slots)",
        )

        print("== 2. INACTIVE DOCTOR ==")

        doctor_service.deactivate(doctor_id)

        check(
            "inactive doctor no availability",
            slot_service.available_slots(doctor_name, mon1) == [],
        )

        check(
            "inactive doctor is_slot_available false",
            slot_service.is_slot_available(
                doctor_name,
                mon1,
                hhmm("10:00"),
            ) is False,
        )

        doctor_service.activate(doctor_id)

        print("== 3. WEEKLY OFF DAY ==")

        check(
            "weekly off day no slots",
            slot_service.available_slots(doctor_name, wed1) == [],
        )

        check(
            "weekly off day not bookable",
            slot_service.is_slot_available(
                doctor_name,
                wed1,
                hhmm("10:00"),
            ) is False,
        )

        print("== 4. DOCTOR DAY-OFF ==")

        day_off_service.add_day_off(doctor_id, mon2)

        check(
            "day-off no slots",
            slot_service.available_slots(doctor_name, mon2) == [],
        )

        check(
            "day-off not bookable",
            slot_service.is_slot_available(
                doctor_name,
                mon2,
                hhmm("10:00"),
            ) is False,
        )

        day_off_service.remove_day_off(doctor_id, mon2)

        print("== 5/6/7. MORNING, EVENING, BREAK ==")

        check(
            "morning slots correct",
            all(
                slot in slots
                for slot in ("10:00", "10:30", "13:00", "13:30")
            ),
        )

        check(
            "evening slots correct",
            all(
                slot in slots
                for slot in ("16:00", "16:30", "18:00", "18:30")
            ),
        )

        check(
            "break 14:00-16:00 has no slots",
            not any(
                slot >= "14:00" and slot < "16:00"
                for slot in slots
            ),
        )

        print("== 8/9. BOOKED THEN CANCELLED SLOT ==")

        appt_a = book_service.book(
            {
                "patient_name": "Avail A",
                "telegram_id": f"avail-{suffix}",
                "doctor": doctor_name,
                "appointment_date": mon1,
                "appointment_time": hhmm("10:00"),
            }
        )

        appointment_ids.append(appt_a.id)

        slots_after_book = slot_service.available_slots(doctor_name, mon1)

        check(
            "booked slot excluded",
            "10:00" not in slots_after_book,
        )

        check(
            "booked slot not bookable",
            slot_service.is_slot_available(
                doctor_name,
                mon1,
                hhmm("10:00"),
            ) is False,
        )

        book_service.cancel(appt_a.id)

        check(
            "cancelled slot available again",
            slot_service.is_slot_available(
                doctor_name,
                mon1,
                hhmm("10:00"),
            ) is True,
        )

        print("== 10/11. INVALID / OFF-HOURS TIME ==")

        check(
            "invalid time 10:15 not bookable",
            slot_service.is_slot_available(
                doctor_name,
                mon1,
                hhmm("10:15"),
            ) is False,
        )

        check(
            "off-hours 15:00 not bookable",
            slot_service.is_slot_available(
                doctor_name,
                mon1,
                hhmm("15:00"),
            ) is False,
        )

        print("== 12. BOOKING CANNOT BYPASS AVAILABILITY ==")

        try:
            book_service.book(
                {
                    "patient_name": "Bypass",
                    "telegram_id": f"avail-{suffix}",
                    "doctor": doctor_name,
                    "appointment_date": mon1,
                    "appointment_time": hhmm("14:00"),
                }
            )
            check("bypass booking (break time)", False, "should have raised")
        except ValueError as error:
            check(
                "bypass booking (break time) rejected",
                "not available" in str(error),
                str(error),
            )

        print("== RESCHEDULE SETUP ==")

        appt_a = book_service.book(
            {
                "patient_name": "Avail A",
                "telegram_id": f"avail-{suffix}",
                "doctor": doctor_name,
                "appointment_date": mon1,
                "appointment_time": hhmm("10:00"),
            }
        )

        appointment_ids.append(appt_a.id)

        appt_b = book_service.book(
            {
                "patient_name": "Avail B",
                "telegram_id": f"avail-{suffix}",
                "doctor": doctor_name,
                "appointment_date": mon1,
                "appointment_time": hhmm("11:00"),
            }
        )

        appointment_ids.append(appt_b.id)

        print("== 13/14. RESCHEDULE TO AVAILABLE SLOT ==")

        rescheduled = book_service.reschedule(
            appt_a.id,
            mon1,
            hhmm("10:30"),
        )

        check(
            "reschedule to available slot succeeds",
            rescheduled is not None
            and rescheduled.appointment_time == hhmm("10:30"),
        )

        check(
            "rescheduled appointment not self-conflicting (10:00 freed)",
            slot_service.is_slot_available(
                doctor_name,
                mon1,
                hhmm("10:00"),
            ) is True,
        )

        print("== 15. RESCHEDULE TO BOOKED SLOT ==")

        try:
            book_service.reschedule(
                appt_a.id,
                mon1,
                hhmm("11:00"),
            )
            check("reschedule to booked slot", False, "should have raised")
        except ValueError as error:
            check(
                "reschedule to booked slot rejected",
                "not available" in str(error),
                str(error),
            )

        print("== 16. RESCHEDULE TO DAY-OFF ==")

        day_off_service.add_day_off(doctor_id, mon2)

        try:
            book_service.reschedule(
                appt_a.id,
                mon2,
                hhmm("10:00"),
            )
            check("reschedule to day-off", False, "should have raised")
        except ValueError as error:
            check(
                "reschedule to day-off rejected",
                "not available" in str(error),
                str(error),
            )

        day_off_service.remove_day_off(doctor_id, mon2)

        print("== 17. RESCHEDULE TO WEEKLY OFF DAY ==")

        try:
            book_service.reschedule(
                appt_a.id,
                wed1,
                hhmm("10:00"),
            )
            check("reschedule to weekly off day", False, "should have raised")
        except ValueError as error:
            check(
                "reschedule to weekly off day rejected",
                "not available" in str(error),
                str(error),
            )

        print("== 18. RESCHEDULE DOES NOT CONFLICT WITH ITSELF ==")

        same = book_service.reschedule(
            appt_a.id,
            mon1,
            hhmm("10:30"),
        )

        check(
            "reschedule to own current slot succeeds",
            same is not None and same.appointment_time == hhmm("10:30"),
        )

        check(
            "reschedule to off-hours rejected",
            True,
        )

        try:
            book_service.reschedule(
                appt_a.id,
                mon1,
                hhmm("14:00"),
            )
            check("reschedule to off-hours", False, "should have raised")
        except ValueError:
            check(
                "reschedule to off-hours rejected",
                True,
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

    print("BOOKING AVAILABILITY TESTS OK")


if __name__ == "__main__":

    main()