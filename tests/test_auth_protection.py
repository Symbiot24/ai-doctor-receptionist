"""Tests for Step 3: JWT protection of the clinic admin API.

Standalone test (the project has no pytest setup):

    python -m tests.test_auth_protection

For every protected endpoint verifies: no Authorization header -> 401,
invalid token -> 401, expired token -> 401, valid token -> success.
Also verifies /api/auth/login stays public and the Telegram booking path
still works. All test rows are removed at the end.
"""

import sys
import time
from datetime import date
from datetime import time as dtime
from datetime import timedelta

from fastapi.testclient import TestClient

from app.api.main import app as api_app
from app.auth.security import create_access_token
from app.database.db import SessionLocal
from app.database.migrations import ensure_admin_users_table
from app.database.models import AdminUser
from app.database.models import Appointment
from app.database.models import Clinic
from app.database.models import ClinicDayOff
from app.database.models import Doctor
from app.database.models import DoctorDayOff
from app.database.models import DoctorSchedule
from app.repositories.appointment_repository import AppointmentRepository
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


def main():

    ensure_admin_users_table()

    db = SessionLocal()

    suffix = str(int(time.time()))

    email = f"protect.admin.{suffix}@clinic.local"

    password = "Protect!Pass-2026"

    admin_id = None

    test_doctor_id = None

    appt_ids = []

    before_clinics = db.query(Clinic).count()

    before_doctors = db.query(Doctor).count()

    before_appts = db.query(Appointment).count()

    try:

        service = AdminService(db)

        admin = service.create_admin(
            email,
            password,
            name="Protect Test Admin",
        )

        admin_id = admin.id

        token = create_access_token(admin.id)

        expired = create_access_token(
            admin.id,
            expires_delta=timedelta(seconds=-5),
        )

        invalid = "invalid.token.value"

        def header(bearer):
            return {"Authorization": f"Bearer {bearer}"}

        print("== LOGIN ENDPOINT STAYS PUBLIC ==")

        public_login = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

        check(
            "login without token -> 200",
            public_login.status_code == 200,
        )

        print("== SETUP: TEST DOCTOR (valid token) ==")

        doctor_name = f"Auth Protect {suffix}"

        create_doctor = client.post(
            "/api/doctors",
            headers=header(token),
            json={
                "name": doctor_name,
                "specialization": "Auth Protect",
            },
        )

        check(
            "create doctor with valid token 201",
            create_doctor.status_code == 201,
            str(create_doctor.status_code),
        )

        test_doctor_id = create_doctor.json()["id"]

        clinic_name = client.get(
            "/api/clinic",
            headers=header(token),
        ).json().get("name")

        tomorrow = date.today() + timedelta(days=7)

        off_date = date.today() + timedelta(days=8)

        avail_date = date.today() + timedelta(days=9)

        repo = AppointmentRepository(db)

        def make_appointment(appointment_time):

            return repo.create(
                {
                    "patient_name": "Protect Appt",
                    "telegram_id": "protecttest",
                    "phone": "9999999999",
                    "doctor": doctor_name,
                    "appointment_date": avail_date,
                    "appointment_time": appointment_time,
                    "status": "BOOKED",
                }
            )

        appt_resched = make_appointment(dtime(9, 0))

        appt_cancel = make_appointment(dtime(9, 30))

        appt_status = make_appointment(dtime(10, 0))

        appt_ids = [
            appt_resched.id,
            appt_cancel.id,
            appt_status.id,
        ]

        cases = [
            ("GET", "/api/clinic", None, 200),
            ("PUT", "/api/clinic", {"name": clinic_name}, 200),
            ("GET", "/api/doctors", None, 200),
            ("GET", f"/api/doctors/{test_doctor_id}", None, 200),
            ("PUT", f"/api/doctors/{test_doctor_id}", {"specialization": "Updated Spec"}, 200),
            ("PATCH", f"/api/doctors/{test_doctor_id}/deactivate", None, 200),
            ("PATCH", f"/api/doctors/{test_doctor_id}/activate", None, 200),
            ("GET", f"/api/doctors/{test_doctor_id}/schedule", None, 200),
            ("PUT", f"/api/doctors/{test_doctor_id}/schedule/monday", {"morning_start": "09:00", "morning_end": "12:00"}, 200),
            ("GET", f"/api/doctors/{test_doctor_id}/day-offs", None, 200),
            ("POST", f"/api/doctors/{test_doctor_id}/day-offs", {"date": str(tomorrow), "reason": "protect"}, 201),
            ("DELETE", f"/api/doctors/{test_doctor_id}/day-offs/{tomorrow}", None, 204),
            ("GET", f"/api/doctors/{test_doctor_id}/availability?date={avail_date}", None, 200),
            ("GET", "/api/clinic/day-offs", None, 200),
            ("POST", "/api/clinic/day-offs", {"date": str(off_date), "reason": "protect"}, 201),
            ("DELETE", f"/api/clinic/day-offs/{off_date}", None, 204),
            ("GET", "/api/appointments", None, 200),
            ("POST", f"/api/appointments/{appt_resched.id}/reschedule", {"appointment_date": str(avail_date), "appointment_time": "10:30"}, 200),
            ("POST", f"/api/appointments/{appt_cancel.id}/cancel", None, 200),
            ("POST", f"/api/appointments/{appt_status.id}/status", {"status": "COMPLETED"}, 200),
            ("GET", "/api/dashboard/summary", None, 200),
            ("POST", "/api/doctors", {"name": f"Auth Protect Dup {suffix}", "specialization": "X"}, 201),
        ]

        print("== UNAUTHORIZED: NO / INVALID / EXPIRED TOKEN ==")

        for method, path, body, _ in cases:

            kwargs = {"json": body} if body is not None else {}

            no_token = client.request(method, path, **kwargs)

            check(
                f"no token  {method} {path} -> 401",
                no_token.status_code == 401,
                str(no_token.status_code),
            )

            bad_token = client.request(
                method,
                path,
                headers=header(invalid),
                **kwargs,
            )

            check(
                f"invalid token {method} {path} -> 401",
                bad_token.status_code == 401,
                str(bad_token.status_code),
            )

            expired_token = client.request(
                method,
                path,
                headers=header(expired),
                **kwargs,
            )

            check(
                f"expired token {method} {path} -> 401",
                expired_token.status_code == 401,
                str(expired_token.status_code),
            )

        print("== AUTHORIZED: VALID TOKEN ==")

        for method, path, body, expected in cases:

            kwargs = {"json": body} if body is not None else {}

            response = client.request(
                method,
                path,
                headers=header(token),
                **kwargs,
            )

            check(
                f"valid token {method} {path} -> {expected}",
                response.status_code == expected,
                str(response.status_code),
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
                    "patient_name": "Auth Protect Test Patient",
                    "telegram_id": "authprotecttest",
                    "phone": "9999999999",
                    "age": 32,
                    "gender": "Male",
                    "symptoms": "auth step 3 regression",
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

        if appt_ids:

            db.query(Appointment).filter(
                Appointment.id.in_(appt_ids)
            ).delete(synchronize_session=False)

        if test_doctor_id is not None:

            db.query(DoctorDayOff).filter(
                DoctorDayOff.doctor_id == test_doctor_id
            ).delete(synchronize_session=False)

            db.query(DoctorSchedule).filter(
                DoctorSchedule.doctor_id == test_doctor_id
            ).delete(synchronize_session=False)

            db.query(Doctor).filter(
                Doctor.id == test_doctor_id
            ).delete(synchronize_session=False)

        db.query(Doctor).filter(
            Doctor.name.like(f"Auth Protect %{suffix}%")
        ).delete(synchronize_session=False)

        db.query(ClinicDayOff).filter(
            ClinicDayOff.date.in_([off_date])
        ).delete(synchronize_session=False)

        if admin_id is not None:

            db.query(AdminUser).filter(
                AdminUser.id == admin_id
            ).delete(synchronize_session=False)

        db.commit()

        after_clinics = db.query(Clinic).count()

        after_doctors = db.query(Doctor).count()

        after_appts = db.query(Appointment).count()

        check(
            "clinic data intact",
            after_clinics == before_clinics,
            f"{before_clinics} -> {after_clinics}",
        )

        check(
            "doctor data intact",
            after_doctors == before_doctors,
            f"{before_doctors} -> {after_doctors}",
        )

        check(
            "appointment data intact",
            after_appts == before_appts,
            f"{before_appts} -> {after_appts}",
        )

        db.close()

    print()
    print(f"PASSED: {len(PASSED)}")
    print(f"FAILED: {len(FAILED)}")

    for label in FAILED:
        print(f"  - {label}")

    if FAILED:
        sys.exit(1)

    print("AUTH PROTECTION TESTS OK")


if __name__ == "__main__":

    main()
