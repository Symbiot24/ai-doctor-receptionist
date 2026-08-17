"""Tests for the admin auth foundation (Step 1).

Standalone test (the project has no pytest setup):

    python -m tests.test_admin_auth

Verifies password hashing/verification, admin creation, duplicate email
handling (service-level and database-level), email/password validation,
email and password updates, and that the existing Telegram booking path
still works. All test rows are removed at the end.
"""

import sys
import time
from datetime import date
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from app.auth.security import hash_password
from app.auth.security import verify_password
from app.database.db import SessionLocal
from app.database.migrations import ensure_admin_users_table
from app.database.models import AdminUser
from app.database.models import Appointment
from app.repositories.admin_repository import AdminRepository
from app.services.admin_service import AdminService
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService

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

    ensure_admin_users_table()

    db = SessionLocal()

    suffix = str(int(time.time()))

    email = f"test.admin.{suffix}@clinic.local"

    password = "S3cure-Pass!word"

    test_admin_id = None

    second_admin_id = None

    try:

        print("== PASSWORD UTILITIES ==")

        hashed = hash_password(password)

        check("hash differs from plaintext", hashed != password)

        check(
            "hash uses argon2id scheme",
            hashed.startswith("$argon2id$"),
        )

        check(
            "correct password -> True",
            verify_password(password, hashed),
        )

        check(
            "incorrect password -> False",
            not verify_password("wrong-password", hashed),
        )

        check(
            "malformed hash -> False",
            not verify_password(password, "not-a-hash"),
        )

        check(
            "empty hash -> False",
            not verify_password(password, ""),
        )

        check(
            "salt differs between hashes",
            hash_password(password) != hashed,
        )

        print("== CREATE ADMIN (service) ==")

        service = AdminService(db)

        admin = service.create_admin(
            email,
            password,
            name="Test Admin",
        )

        test_admin_id = admin.id

        check("admin created with id", admin.id is not None)

        check("email stored lowercased", admin.email == email)

        check("name stored", admin.name == "Test Admin")

        check("is_active defaults true", admin.is_active is True)

        check("created_at set", admin.created_at is not None)

        check("password_hash exists", bool(admin.password_hash))

        check(
            "password NOT stored in plaintext",
            password not in admin.password_hash,
        )

        check(
            "stored hash verifies correct password",
            service.check_password(admin, password),
        )

        check(
            "wrong password rejected",
            not service.check_password(admin, "wrong-password"),
        )

        found = service.get_by_email(email.upper())

        check(
            "get_by_email case-insensitive",
            found is not None and found.id == admin.id,
        )

        by_id = service.get_by_id(admin.id)

        check(
            "get_by_id works",
            by_id is not None and by_id.email == email,
        )

        print("== DUPLICATE EMAIL HANDLING ==")

        try:
            service.create_admin(
                email,
                "Another-Pass-123",
                name="Dup",
            )
            check("duplicate email rejected (service)", False, "no error")
        except ValueError as error:
            check(
                "duplicate email rejected (service)",
                "already exists" in str(error),
            )

        try:
            service.create_admin(
                email.upper(),
                "Another-Pass-123",
                name="DupCI",
            )
            check("case-variant duplicate rejected (service)", False, "no error")
        except ValueError as error:
            check(
                "case-variant duplicate rejected (service)",
                "already exists" in str(error),
            )

        repository = AdminRepository(db)

        try:
            repository.create(
                {
                    "email": email,
                    "password_hash": "x",
                    "name": "DB",
                }
            )
            check("DB unique constraint blocks duplicate", False, "no error")
        except IntegrityError:
            db.rollback()
            check("DB unique constraint blocks duplicate", True)

        try:
            repository.create(
                {
                    "email": email.upper(),
                    "password_hash": "x",
                    "name": "DBCI",
                }
            )
            check("DB CI index blocks case-variant duplicate", False, "no error")
        except IntegrityError:
            db.rollback()
            check("DB CI index blocks case-variant duplicate", True)

        print("== VALIDATION ==")

        for bad_email in ("not-an-email", "a@b", ""):

            try:
                service.create_admin(
                    bad_email,
                    "Some-Pass-123",
                    name="X",
                )
                check(
                    f"invalid email rejected ({bad_email!r})",
                    False,
                    "no error",
                )
            except ValueError:
                check(
                    f"invalid email rejected ({bad_email!r})",
                    True,
                )

        try:
            service.create_admin(
                f"other.{suffix}@clinic.local",
                "short",
                name="X",
            )
            check("short password rejected", False, "no error")
        except ValueError as error:
            check(
                "short password rejected",
                "at least 8" in str(error),
            )

        print("== UPDATE EMAIL ==")

        new_email = f"renamed.{suffix}@clinic.local"

        updated = service.update_email(admin.id, new_email)

        check("update_email works", updated.email == new_email)

        check(
            "get_by_email finds new email",
            service.get_by_email(new_email) is not None,
        )

        check(
            "old email no longer found",
            service.get_by_email(email) is None,
        )

        second = service.create_admin(
            f"second.{suffix}@clinic.local",
            "Another-Pass-123",
            name="Second",
        )

        second_admin_id = second.id

        try:
            service.update_email(admin.id, second.email)
            check("update_email to existing email rejected", False, "no error")
        except ValueError as error:
            check(
                "update_email to existing email rejected",
                "already exists" in str(error),
            )

        try:
            service.update_email(admin.id, "bad-email")
            check("update_email invalid email rejected", False, "no error")
        except ValueError:
            check("update_email invalid email rejected", True)

        print("== UPDATE PASSWORD ==")

        new_password = "New-S3cure!Pass-99"

        updated_pw = service.update_password(admin.id, new_password)

        check("update_password works", bool(updated_pw.password_hash))

        check(
            "old password no longer verifies",
            not service.check_password(admin, password),
        )

        check(
            "new password verifies",
            service.check_password(admin, new_password),
        )

        print("== TELEGRAM BOOKING STILL WORKS ==")

        slot_service = SlotService(db)

        doctor_service = DoctorService(db)

        active_doctors = doctor_service.get_all()

        check("active doctors exist", bool(active_doctors))

        doctor = active_doctors[0]

        print(f"  probing doctor: {doctor.name}")

        probe_date = date.today() + timedelta(days=10)

        slots = []

        for _ in range(21):

            slots = slot_service.available_slots(
                doctor.name,
                probe_date,
            )

            if slots:
                break

            probe_date += timedelta(days=1)

        check("slots available for booking", bool(slots), str(len(slots)))

        if slots:

            booking = AppointmentService(db).book(
                {
                    "patient_name": "Auth Test Patient",
                    "telegram_id": "authtest",
                    "phone": "9999999999",
                    "age": 30,
                    "gender": "Male",
                    "symptoms": "auth step 1 regression",
                    "doctor": doctor.name,
                    "appointment_date": probe_date,
                    "appointment_time": slots[0],
                    "status": "BOOKED",
                }
            )

            check("booking succeeds", booking.id is not None)

            check(
                "booking resolves clinic_id",
                booking.clinic_id is not None,
            )

            db.query(Appointment).filter(
                Appointment.id == booking.id
            ).delete()

            db.commit()

            print("  cleanup: deleted probe appointment")

    finally:

        if second_admin_id is not None:

            db.query(AdminUser).filter(
                AdminUser.id == second_admin_id
            ).delete()

        if test_admin_id is not None:

            db.query(AdminUser).filter(
                AdminUser.id == test_admin_id
            ).delete()

        db.commit()

        db.close()

    print()
    print(f"PASSED: {len(PASSED)}")
    print(f"FAILED: {len(FAILED)}")

    for label in FAILED:
        print(f"  - {label}")

    if FAILED:
        sys.exit(1)

    print("ADMIN AUTH TESTS OK")


if __name__ == "__main__":

    main()
