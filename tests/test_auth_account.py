"""Tests for Step 4: authenticated admin account management.

Standalone test (the project has no pytest setup):

    python -m tests.test_auth_account

Covers: GET /api/auth/me (valid/no/invalid token), PUT /api/auth/profile
(name/email updates, invalid email, duplicate email, nothing to update,
unauth), PUT /api/auth/password (correct/incorrect current, mismatch,
weak, reuse, unauth, old password stops working, new password works),
and the regression probes (doctors, slots, Telegram booking, data intact).
All test rows are removed at the end.
"""

import sys
import time
from datetime import date
from datetime import timedelta

from fastapi.testclient import TestClient

from app.api.main import app as api_app
from app.database.db import SessionLocal
from app.database.migrations import ensure_admin_users_table
from app.database.models import AdminUser
from app.database.models import Appointment
from app.services.admin_service import AdminService
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService

PASSED = []
FAILED = []

client = TestClient(api_app)


def check(label, condition, detail=""):
    if condition:
        PASSED.append(label)
        print(f"  PASS  {label} {detail}")
    else:
        FAILED.append(label)
        print(f"  FAIL  {label} {detail}")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def tamper(token):
    return token[:-1] + ("b" if token[-1] != "b" else "c")


def main():

    ensure_admin_users_table()

    db = SessionLocal()

    suffix = str(int(time.time()))

    primary_email = f"account.admin.{suffix}@clinic.local"
    other_email = f"other.admin.{suffix}@clinic.local"
    password = "Account-S3cure!Pass"
    new_password = "Brand-New-Pass-2026!"

    primary_id = None
    other_id = None

    try:

        service = AdminService(db)

        baseline_doctors = len(
            DoctorService(db).get_all_including_inactive()
        )
        baseline_active_doctors = len(DoctorService(db).get_all())
        baseline_appointments = db.query(Appointment).count()

        admin = service.create_admin(
            primary_email,
            password,
            name="Account Test Admin",
        )

        primary_id = admin.id

        other = service.create_admin(
            other_email,
            "Other-S3cure!Pass",
            name="Other Admin",
        )

        other_id = other.id

        login = client.post(
            "/api/auth/login",
            json={"email": primary_email, "password": password},
        )

        token = login.json().get("access_token")

        other_login = client.post(
            "/api/auth/login",
            json={"email": other_email, "password": "Other-S3cure!Pass"},
        )

        other_token = other_login.json().get("access_token")

        check("setup: login works", login.status_code == 200 and bool(token))

        print("== GET /api/auth/me ==")

        me = client.get("/api/auth/me", headers=auth(token))

        me_body = me.json()

        check(
            "valid JWT -> 200",
            me.status_code == 200,
            str(me.status_code),
        )

        check(
            "me has id",
            me_body.get("id") == admin.id,
            str(me_body.get("id")),
        )

        check(
            "me has name",
            me_body.get("name") == "Account Test Admin",
        )

        check(
            "me has email",
            me_body.get("email") == primary_email,
        )

        check(
            "me has is_active true",
            me_body.get("is_active") is True,
        )

        check(
            "password_hash NOT in response",
            "password_hash" not in me.text,
        )

        me_no_token = client.get("/api/auth/me")

        check(
            "no JWT -> 401",
            me_no_token.status_code == 401,
            str(me_no_token.status_code),
        )

        me_invalid = client.get(
            "/api/auth/me",
            headers=auth("not.a.real.token"),
        )

        check(
            "invalid JWT -> 401",
            me_invalid.status_code == 401,
            str(me_invalid.status_code),
        )

        print("== PUT /api/auth/profile ==")

        name_change = client.put(
            "/api/auth/profile",
            headers=auth(token),
            json={"name": "Updated Admin Name"},
        )

        check(
            "valid name change -> 200",
            name_change.status_code == 200,
            str(name_change.status_code),
        )

        check(
            "name change reflected",
            name_change.json().get("name") == "Updated Admin Name",
        )

        new_email = f"renamed.admin.{suffix}@clinic.local"

        email_change = client.put(
            "/api/auth/profile",
            headers=auth(token),
            json={"email": new_email},
        )

        check(
            "valid email change -> 200",
            email_change.status_code == 200,
            str(email_change.status_code),
        )

        check(
            "email change reflected (normalized lowercase)",
            email_change.json().get("email") == new_email,
        )

        login_after_email = client.post(
            "/api/auth/login",
            json={"email": new_email.upper(), "password": password},
        )

        check(
            "old email no longer used, new email login works",
            login_after_email.status_code == 200,
            str(login_after_email.status_code),
        )

        invalid_email = client.put(
            "/api/auth/profile",
            headers=auth(token),
            json={"email": "not-an-email"},
        )

        check(
            "invalid email -> validation error",
            invalid_email.status_code == 400,
            str(invalid_email.status_code),
        )

        duplicate_email = client.put(
            "/api/auth/profile",
            headers=auth(token),
            json={"email": other_email},
        )

        check(
            "duplicate email -> rejected",
            duplicate_email.status_code == 400,
            str(duplicate_email.status_code),
        )

        nothing = client.put(
            "/api/auth/profile",
            headers=auth(token),
            json={},
        )

        check(
            "nothing to update -> 400",
            nothing.status_code == 400,
            str(nothing.status_code),
        )

        unauth_profile = client.put(
            "/api/auth/profile",
            json={"name": "Hacker"},
        )

        check(
            "unauthenticated profile -> 401",
            unauth_profile.status_code == 401,
            str(unauth_profile.status_code),
        )

        empty_name = client.put(
            "/api/auth/profile",
            headers=auth(token),
            json={"name": "   "},
        )

        check(
            "blank name -> rejected",
            empty_name.status_code == 400,
            str(empty_name.status_code),
        )

        me_after_profile = client.get("/api/auth/me", headers=auth(token))

        check(
            "me reflects updated name",
            me_after_profile.json().get("name") == "Updated Admin Name",
        )

        print("== PUT /api/auth/password ==")

        good_change = client.put(
            "/api/auth/password",
            headers=auth(token),
            json={
                "current_password": password,
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )

        check(
            "correct current + valid new -> 200",
            good_change.status_code == 200,
            str(good_change.status_code),
        )

        wrong_current = client.put(
            "/api/auth/password",
            headers=auth(token),
            json={
                "current_password": "Wrong-Current-Pass",
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )

        check(
            "incorrect current password -> rejected",
            wrong_current.status_code == 400,
            str(wrong_current.status_code),
        )

        mismatch = client.put(
            "/api/auth/password",
            headers=auth(token),
            json={
                "current_password": new_password,
                "new_password": "Another-New-Pass-1",
                "confirm_password": "Different-Confirm-1",
            },
        )

        check(
            "mismatched confirmation -> rejected",
            mismatch.status_code == 400,
            str(mismatch.status_code),
        )

        weak = client.put(
            "/api/auth/password",
            headers=auth(token),
            json={
                "current_password": new_password,
                "new_password": "short",
                "confirm_password": "short",
            },
        )

        check(
            "weak password -> rejected",
            weak.status_code == 400,
            str(weak.status_code),
        )

        reuse = client.put(
            "/api/auth/password",
            headers=auth(token),
            json={
                "current_password": new_password,
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )

        check(
            "new password reusing current -> rejected",
            reuse.status_code == 400,
            str(reuse.status_code),
        )

        unauth_password = client.put(
            "/api/auth/password",
            json={
                "current_password": new_password,
                "new_password": "Something-Else-1",
                "confirm_password": "Something-Else-1",
            },
        )

        check(
            "unauthenticated password -> 401",
            unauth_password.status_code == 401,
            str(unauth_password.status_code),
        )

        old_pw_login = client.post(
            "/api/auth/login",
            json={"email": new_email, "password": password},
        )

        check(
            "old password no longer authenticates",
            old_pw_login.status_code == 401,
            str(old_pw_login.status_code),
        )

        new_pw_login = client.post(
            "/api/auth/login",
            json={"email": new_email, "password": new_password},
        )

        new_token = new_pw_login.json().get("access_token")

        check(
            "new password authenticates",
            new_pw_login.status_code == 200 and bool(new_token),
            str(new_pw_login.status_code),
        )

        me_with_new_token = client.get(
            "/api/auth/me",
            headers=auth(new_token),
        )

        check(
            "me works with new token",
            me_with_new_token.status_code == 200,
            str(me_with_new_token.status_code),
        )

        check(
            "old token still usable until expiry (stateless JWT, documented)",
            client.get("/api/auth/me", headers=auth(token)).status_code == 200,
        )

        check(
            "no plaintext password stored",
            db.query(AdminUser).filter(
                AdminUser.id == primary_id
            ).first().password_hash.startswith("$argon2id$"),
        )

        print("== REGRESSION: DATA INTACT ==")

        doctor_service = DoctorService(db)

        check(
            "doctors intact",
            len(doctor_service.get_all_including_inactive())
            == baseline_doctors,
            str(len(doctor_service.get_all_including_inactive())),
        )

        check(
            "active doctors still work",
            len(doctor_service.get_all()) == baseline_active_doctors,
            str(len(doctor_service.get_all())),
        )

        slot_service = SlotService(db)

        doctor = doctor_service.get_all()[0]

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
                    "patient_name": "Auth Account Test Patient",
                    "telegram_id": "authaccounttest",
                    "phone": "8888888888",
                    "age": 29,
                    "gender": "Female",
                    "symptoms": "auth step 4 regression",
                    "doctor": doctor.name,
                    "appointment_date": probe_date,
                    "appointment_time": slots[0],
                    "status": "BOOKED",
                }
            )

            check("Telegram booking still works", booking.id is not None)

            db.query(Appointment).filter(
                Appointment.id == booking.id
            ).delete()

            db.commit()

            print("  cleanup: deleted probe appointment")

        check(
            "appointments intact",
            db.query(Appointment).count() == baseline_appointments,
            str(db.query(Appointment).count()),
        )

    finally:

        if other_id is not None:

            db.query(AdminUser).filter(
                AdminUser.id == other_id
            ).delete(synchronize_session=False)

        if primary_id is not None:

            db.query(AdminUser).filter(
                AdminUser.id == primary_id
            ).delete(synchronize_session=False)

        db.commit()

        db.expire_all()

        check(
            "test admins removed",
            service.get_by_email(f"renamed.admin.{suffix}@clinic.local")
            is None
            and service.get_by_email(other_email) is None,
        )

        db.close()

    print()
    print(f"PASSED: {len(PASSED)}")
    print(f"FAILED: {len(FAILED)}")

    for label in FAILED:
        print(f"  - {label}")

    if FAILED:
        sys.exit(1)

    print("AUTH ACCOUNT TESTS OK")


if __name__ == "__main__":

    main()
