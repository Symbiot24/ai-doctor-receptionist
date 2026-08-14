"""Focused tests for Doctor Management.

Runnable standalone (project has no pytest setup):

    python -m tests.test_doctor_management

Creates a uniquely-named test doctor against the real database, verifies
the Doctor Management layer, and cleans up all test rows afterwards.
"""

import sys
import time
from datetime import date
from datetime import datetime
from datetime import timedelta

from app.database.db import SessionLocal
from app.database.migrations import ensure_doctor_clinic_assignment
from app.services.doctor_service import DoctorService
from app.services.clinic_service import ClinicService
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


def main():

    ensure_doctor_clinic_assignment()

    db = SessionLocal()

    suffix = str(int(time.time()))

    doctor_name = f"Dr Test {suffix}"

    created_id = None

    appointment_id = None

    try:

        service = DoctorService(db)

        clinic_service = ClinicService(db)

        clinic = clinic_service.get_active() or clinic_service.get()

        clinic_id = clinic.id

        print("== CREATE DOCTOR ==")

        doctor = service.create(
            {
                "name": doctor_name,
                "specialization": "General Medicine",
                "consultation_fee": 500,
                "morning_start": "10:00",
                "morning_end": "14:00",
                "evening_start": "16:00",
                "evening_end": "19:00",
            }
        )

        created_id = doctor.id

        check(
            "create doctor",
            doctor.id is not None and doctor.name == doctor_name,
            f"(id={doctor.id})",
        )

        check(
            "clinic association",
            doctor.clinic_id == clinic_id,
            f"(doctor.clinic_id={doctor.clinic_id}, clinic.id={clinic_id})",
        )

        check(
            "active default YES",
            doctor.active == "YES",
        )

        print("== GET DOCTOR ==")

        fetched = service.get_by_id(doctor.id)

        check(
            "get doctor",
            fetched is not None and fetched.id == doctor.id,
        )

        print("== LIST DOCTORS ==")

        all_names = [d.name for d in service.get_all()]

        check(
            "list doctors",
            doctor_name in all_names,
            f"(active count={len(all_names)})",
        )

        print("== UPDATE DOCTOR ==")

        updated = service.update(
            doctor.id,
            {
                "name": f"{doctor_name} Jr",
                "consultation_fee": 600,
                "evening_start": "17:00",
            },
        )

        check(
            "update doctor",
            updated is not None
            and updated.consultation_fee == 600
            and updated.name == f"{doctor_name} Jr",
        )

        print("== ACTIVE FILTERING / DEACTIVATE / ACTIVATE ==")

        active_names = [d.name for d in service.get_active()]

        check(
            "active doctors filtering",
            f"{doctor_name} Jr" in active_names,
        )

        inactive = service.deactivate(doctor.id)

        check(
            "deactivate doctor",
            inactive is not None and inactive.active == "NO",
        )

        check(
            "deactivated removed from selection",
            f"{doctor_name} Jr" not in [d.name for d in service.get_all()],
        )

        active = service.activate(doctor.id)

        check(
            "activate doctor",
            active is not None and active.active == "YES",
        )

        check(
            "activated back in selection",
            f"{doctor_name} Jr" in [d.name for d in service.get_all()],
        )

        print("== VALIDATION ==")

        try:
            service.create(
                {"name": "Dr Bad", "specialization": "X", "consultation_fee": -10}
            )
            check("invalid consultation fee", False, "should have raised")
        except ValueError as error:
            check(
                "invalid consultation fee",
                "consultation_fee" in str(error),
                str(error),
            )

        try:
            service.create(
                {
                    "name": "Dr Bad",
                    "specialization": "X",
                    "morning_start": "14:00",
                    "morning_end": "10:00",
                }
            )
            check("invalid shift range", False, "should have raised")
        except ValueError as error:
            check(
                "invalid shift range",
                "end must be after start" in str(error),
                str(error),
            )

        try:
            service.create({"name": "   "})
            check("required fields", False, "should have raised")
        except ValueError as error:
            check(
                "required fields",
                "name is required" in str(error)
                and "specialization is required" in str(error),
                str(error),
            )

        print("== REGRESSION: EXISTING SYSTEM ==")

        check(
            "existing active doctors present",
            any(
                d.name in ("Dr Sharma", "Dr Mehta", "Dr Khan", "Dr Batra")
                for d in service.get_all()
            ),
        )

        day = (datetime.now().date() + timedelta(days=7))

        slot_service = SlotService(db)

        slots = slot_service.available_slots(f"{doctor_name} Jr", day)

        check(
            "slot generation from morning/evening shifts",
            len(slots) > 0,
            f"({len(slots)} slots)",
        )

        book_service = AppointmentService(db)

        appointment = book_service.book(
            {
                "patient_name": "Regression Patient",
                "telegram_id": f"reg-{suffix}",
                "doctor": f"{doctor_name} Jr",
                "appointment_date": day,
                "appointment_time": datetime.strptime(slots[0], "%H:%M").time(),
            }
        )

        appointment_id = appointment.id

        check(
            "existing booking succeeds with clinic_id",
            appointment.id is not None and appointment.clinic_id == clinic_id,
            f"(appointment.clinic_id={appointment.clinic_id})",
        )

        service.deactivate(doctor.id)

        still_there = book_service.get_by_id(appointment_id)

        check(
            "appointments preserved after deactivation",
            still_there is not None,
        )

        cancel_result = book_service.cancel(appointment_id)

        check(
            "cancellation still works",
            cancel_result is not None and cancel_result.status == "CANCELLED",
        )

    finally:

        db.rollback()

        if appointment_id is not None:
            appointment = db.get(
                __import__(
                    "app.database.models",
                    fromlist=["Appointment"],
                ).Appointment,
                appointment_id,
            )
            if appointment is not None:
                db.delete(appointment)
                db.commit()

        if created_id is not None:
            doctor_row = db.get(
                __import__(
                    "app.database.models",
                    fromlist=["Doctor"],
                ).Doctor,
                created_id,
            )
            if doctor_row is not None:
                db.delete(doctor_row)
                db.commit()

        db.close()

    print()
    print(f"PASSED: {len(PASSED)}")
    print(f"FAILED: {len(FAILED)}")

    for label in FAILED:
        print(f"  - {label}")

    if FAILED:
        sys.exit(1)

    print("DOCTOR MANAGEMENT TESTS OK")


if __name__ == "__main__":

    main()