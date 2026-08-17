"""Tests for Step 2: admin login with JWT.

Standalone test (the project has no pytest setup):

    python -m tests.test_auth_login

Covers: valid login, wrong password, nonexistent email, case-insensitive
email, inactive admin, missing fields, token decode, expired/tampered
tokens, missing Authorization header via get_current_admin(), and the
Telegram booking regression. All test rows are removed at the end.
"""

import sys
import time
from datetime import date
from datetime import timedelta

from fastapi import Depends
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_admin
from app.api.main import app as api_app
from app.auth.security import create_access_token
from app.auth.security import decode_access_token
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


def make_temp_protected_app():

    temp_app = FastAPI()

    @temp_app.get("/protected")
    def protected(admin=Depends(get_current_admin)):
        return {"admin_id": admin.id}

    return TestClient(temp_app)


def tamper(token):
    return token[:-1] + ("b" if token[-1] != "b" else "c")


def main():

    ensure_admin_users_table()

    db = SessionLocal()

    suffix = str(int(time.time()))

    email = f"login.admin.{suffix}@clinic.local"

    password = "S3cure-Login!Pass"

    admin_id = None

    inactive_id = None

    protected_client = make_temp_protected_app()

    try:

        service = AdminService(db)

        admin = service.create_admin(
            email,
            password,
            name="Login Test Admin",
        )

        admin_id = admin.id

        print("== LOGIN: VALID CREDENTIALS ==")

        response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        token = None

        check(
            "valid login -> 200",
            response.status_code == 200,
            str(response.status_code),
        )

        body = response.json()

        check(
            "response contains access_token",
            bool(body.get("access_token")),
        )

        check(
            "token_type is bearer",
            body.get("token_type") == "bearer",
        )

        check(
            "password_hash not exposed",
            "password_hash" not in response.text,
        )

        token = body.get("access_token")

        print("== LOGIN: NEGATIVE CASES ==")

        wrong_pw = client.post(
            "/api/auth/login",
            json={"email": email, "password": "Wrong-Pass-999"},
        )

        check(
            "wrong password -> 401",
            wrong_pw.status_code == 401,
        )

        missing_email = client.post(
            "/api/auth/login",
            json={"email": "nobody@clinic.local", "password": password},
        )

        check(
            "nonexistent email -> 401",
            missing_email.status_code == 401,
        )

        check(
            "generic error message",
            missing_email.json().get("detail") == "Invalid email or password.",
        )

        case_insensitive = client.post(
            "/api/auth/login",
            json={"email": email.upper(), "password": password},
        )

        check(
            "case-insensitive email login -> 200",
            case_insensitive.status_code == 200,
        )

        inactive = service.create_admin(
            f"inactive.{suffix}@clinic.local",
            "Inactive-Pass-123",
            name="Inactive Admin",
        )

        inactive_id = inactive.id

        inactive.is_active = False

        db.commit()

        inactive_login = client.post(
            "/api/auth/login",
            json={
                "email": inactive.email,
                "password": "Inactive-Pass-123",
            },
        )

        check(
            "inactive admin -> 401",
            inactive_login.status_code == 401,
        )

        missing_email_field = client.post(
            "/api/auth/login",
            json={"password": password},
        )

        check(
            "missing email -> 422",
            missing_email_field.status_code == 422,
        )

        missing_password_field = client.post(
            "/api/auth/login",
            json={"email": email},
        )

        check(
            "missing password -> 422",
            missing_password_field.status_code == 422,
        )

        print("== TOKEN DECODE / VALIDATION ==")

        decoded_id = None

        try:
            decoded_id = decode_access_token(token)
        except ValueError as error:
            print("  decode error:", error)

        check(
            "decode valid token -> admin id",
            decoded_id == admin_id,
        )

        expired_token = create_access_token(
            admin_id,
            expires_delta=timedelta(seconds=-5),
        )

        expired_rejected = False

        try:
            decode_access_token(expired_token)
        except ValueError:
            expired_rejected = True

        check("expired token rejected", expired_rejected)

        tampered_rejected = False

        try:
            decode_access_token(tamper(token))
        except ValueError:
            tampered_rejected = True

        check("tampered token rejected", tampered_rejected)

        garbage_rejected = False

        try:
            decode_access_token("not.a.jwt")
        except ValueError:
            garbage_rejected = True

        check("garbage token rejected", garbage_rejected)

        print("== get_current_admin() PROTECTED ENDPOINT ==")

        valid_ok = protected_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

        check(
            "valid token accepted",
            valid_ok.status_code == 200
            and valid_ok.json().get("admin_id") == admin_id,
        )

        no_header = protected_client.get("/protected")

        check(
            "missing Authorization header -> 401",
            no_header.status_code == 401,
        )

        expired_ok = protected_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        check(
            "expired token on endpoint -> 401",
            expired_ok.status_code == 401,
        )

        tampered_ok = protected_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {tamper(token)}"},
        )

        check(
            "tampered token on endpoint -> 401",
            tampered_ok.status_code == 401,
        )

        deleted_ok = protected_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {create_access_token(999999)}"},
        )

        check(
            "deleted admin token -> 401",
            deleted_ok.status_code == 401,
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
                    "patient_name": "Auth Login Test Patient",
                    "telegram_id": "authlogintest",
                    "phone": "9999999999",
                    "age": 31,
                    "gender": "Male",
                    "symptoms": "auth step 2 regression",
                    "doctor": doctor.name,
                    "appointment_date": probe_date,
                    "appointment_time": slots[0],
                    "status": "BOOKED",
                }
            )

            check("booking succeeds", booking.id is not None)

            db.query(Appointment).filter(
                Appointment.id == booking.id
            ).delete()

            db.commit()

            print("  cleanup: deleted probe appointment")

    finally:

        if inactive_id is not None:

            db.query(AdminUser).filter(
                AdminUser.id == inactive_id
            ).delete()

        if admin_id is not None:

            db.query(AdminUser).filter(
                AdminUser.id == admin_id
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

    print("AUTH LOGIN TESTS OK")


if __name__ == "__main__":

    main()
