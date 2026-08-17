"""Idempotent schema migrations applied automatically at app startup."""

from sqlalchemy import inspect
from sqlalchemy import text

from app.database.db import engine

_REMINDER_COLUMNS = {
    "reminder_24h_sent": "BOOLEAN DEFAULT FALSE",
    "reminder_1h_sent": "BOOLEAN DEFAULT FALSE",
}


def ensure_reminder_columns():
    """Add the reminder-tracking columns to appointments if missing.

    Safe to call on every startup (existing rows get DEFAULT FALSE).
    """
    with engine.begin() as conn:

        columns = {
            column["name"]
            for column in inspect(conn).get_columns("appointments")
        }

        for column, column_type in _REMINDER_COLUMNS.items():

            if column not in columns:

                conn.execute(
                    text(
                        f"ALTER TABLE appointments ADD COLUMN {column} {column_type}"
                    )
                )


_CLINIC_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS clinics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    phone VARCHAR(20),
    address VARCHAR(255),
    active VARCHAR(10) DEFAULT 'YES',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
)
"""

_CLINIC_SINGLETON_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION enforce_single_clinic() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF EXISTS (SELECT 1 FROM clinics) THEN
            RAISE EXCEPTION 'Only one clinic record is allowed.';
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.id <> OLD.id THEN
            RAISE EXCEPTION 'Clinic id cannot be changed.';
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        IF (SELECT COUNT(*) FROM clinics) <= 1 THEN
            RAISE EXCEPTION 'The last clinic record cannot be deleted.';
        END IF;
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

_CLINIC_SINGLETON_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS trg_single_clinic ON clinics;
CREATE TRIGGER trg_single_clinic
BEFORE INSERT OR UPDATE OR DELETE ON clinics
FOR EACH ROW EXECUTE FUNCTION enforce_single_clinic();
"""


def ensure_clinic_table():
    """Create the clinics table and add missing columns if needed.

    Safe to call on every startup:
    - CREATE TABLE IF NOT EXISTS is a no-op when the table already exists.
    - ALTER TABLE adds only the columns that are missing.
    """
    with engine.begin() as conn:

        if "clinics" not in inspect(conn).get_table_names():

            conn.execute(text(_CLINIC_TABLE_SQL))

        else:

            columns = {
                column["name"]
                for column in inspect(conn).get_columns("clinics")
            }

            if "updated_at" not in columns:

                conn.execute(
                    text(
                        "ALTER TABLE clinics ADD COLUMN updated_at "
                        "TIMESTAMPTZ DEFAULT now()"
                    )
                )


def ensure_single_clinic():
    """Enforce exactly one clinic record (single-clinic architecture).

    - 0 clinics : seed a default clinic record.
    - 1 clinic  : ensure the singleton trigger exists (no-op).
    - >1 clinics: one-time repair - retain the earliest clinic (lowest id,
      the primary clinic in this system), reassign every doctor and
      appointment to it, delete the duplicate clinic records, then install
      the singleton trigger.

    The trigger is the database-level protection: once installed, a second
    clinic record cannot be inserted (and the last record cannot be
    deleted, and the id cannot change). After this cleanup the merge branch
    is effectively dead code, because the trigger prevents new duplicates.

    Retained clinic is chosen as MIN(id), which in this system is the
    original clinic referenced by all real doctors and appointments.
    """
    with engine.begin() as conn:

        clinic_ids = [
            row[0]
            for row in conn.execute(
                text("SELECT id FROM clinics ORDER BY id")
            )
        ]

        if not clinic_ids:

            conn.execute(
                text(
                    "INSERT INTO clinics (name, description) VALUES "
                    "('My Clinic', 'Default clinic record')"
                )
            )

        elif len(clinic_ids) > 1:

            retain_id = clinic_ids[0]

            conn.execute(
                text(
                    "UPDATE doctors SET clinic_id = :clinic_id "
                    "WHERE clinic_id IS NOT NULL "
                    "AND clinic_id <> :clinic_id"
                ),
                {"clinic_id": retain_id},
            )

            conn.execute(
                text(
                    "UPDATE appointments SET clinic_id = :clinic_id "
                    "WHERE clinic_id IS NOT NULL "
                    "AND clinic_id <> :clinic_id"
                ),
                {"clinic_id": retain_id},
            )

            conn.execute(
                text(
                    "DELETE FROM clinics WHERE id <> :clinic_id"
                ),
                {"clinic_id": retain_id},
            )

        conn.execute(text(_CLINIC_SINGLETON_FUNCTION_SQL))

        conn.execute(text(_CLINIC_SINGLETON_TRIGGER_SQL))


def ensure_doctor_clinic_assignment():
    """Backfill clinic_id on doctors from the single clinic.

    Safety net: existing doctors created before clinic association are
    linked to the single clinic. No-op when every doctor already has a
    clinic_id. Does not touch appointments.
    """
    with engine.begin() as conn:

        unassigned = conn.execute(
            text("SELECT COUNT(*) FROM doctors WHERE clinic_id IS NULL")
        ).scalar()

        if unassigned > 0:

            clinic_id = conn.execute(
                text(
                    "SELECT id FROM clinics "
                    "ORDER BY id LIMIT 1"
                )
            ).scalar()

            if clinic_id is not None:

                conn.execute(
                    text(
                        "UPDATE doctors SET clinic_id = :clinic_id "
                        "WHERE clinic_id IS NULL"
                    ),
                    {"clinic_id": clinic_id},
                )


_DOCTOR_SCHEDULE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS doctor_schedules (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
    day_of_week INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    morning_start TIME,
    morning_end TIME,
    evening_start TIME,
    evening_end TIME,
    CONSTRAINT uq_doctor_schedule_day UNIQUE (doctor_id, day_of_week)
)
"""


def ensure_doctor_schedule_table():
    """Create the doctor_schedules table and backfill from current shifts.

    Safe to call on every startup:
    - CREATE TABLE IF NOT EXISTS is a no-op when the table already exists.
    - Adds the (doctor_id, day_of_week) unique constraint if missing.
    - Backfills one row per weekday for doctors that have no schedule yet,
      copying their existing morning/evening shift fields. Does not delete
      or modify any existing schedule or doctor data.
    """
    with engine.begin() as conn:

        if "doctor_schedules" not in inspect(conn).get_table_names():

            conn.execute(text(_DOCTOR_SCHEDULE_TABLE_SQL))

        else:

            constraints = {
                row[0]
                for row in conn.execute(
                    text(
                        "SELECT conname FROM pg_constraint "
                        "WHERE conrelid = 'doctor_schedules'::regclass"
                    )
                )
            }

            if "uq_doctor_schedule_day" not in constraints:

                conn.execute(
                    text(
                        "ALTER TABLE doctor_schedules ADD CONSTRAINT "
                        "uq_doctor_schedule_day UNIQUE (doctor_id, day_of_week)"
                    )
                )

        doctors = conn.execute(
            text(
                "SELECT d.id, d.morning_start, d.morning_end, "
                "d.evening_start, d.evening_end "
                "FROM doctors d "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM doctor_schedules s WHERE s.doctor_id = d.id"
                ")"
            )
        ).fetchall()

        for row in doctors:

            doctor_id, morning_start, morning_end, evening_start, evening_end = row

            has_shift = bool(morning_start or evening_start)

            for day in range(7):

                conn.execute(
                    text(
                        "INSERT INTO doctor_schedules "
                        "(doctor_id, day_of_week, enabled, morning_start, "
                        "morning_end, evening_start, evening_end) "
                        "VALUES (:doctor_id, :day, :enabled, "
                        ":morning_start, :morning_end, :evening_start, :evening_end)"
                    ),
                    {
                        "doctor_id": doctor_id,
                        "day": day,
                        "enabled": has_shift,
                        "morning_start": morning_start,
                        "morning_end": morning_end,
                        "evening_start": evening_start,
                        "evening_end": evening_end,
                    },
                )


_DOCTOR_DAY_OFF_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS doctor_day_offs (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
    date DATE NOT NULL,
    reason VARCHAR(255),
    CONSTRAINT uq_doctor_day_off UNIQUE (doctor_id, date)
)
"""


def ensure_doctor_day_off_table():
    """Create the doctor_day_offs table and ensure the unique constraint.

    Safe to call on every startup:
    - CREATE TABLE IF NOT EXISTS is a no-op when the table already exists.
    - Adds the (doctor_id, date) unique constraint if missing so a doctor
      cannot have the same day off twice.
    """
    with engine.begin() as conn:

        if "doctor_day_offs" not in inspect(conn).get_table_names():

            conn.execute(text(_DOCTOR_DAY_OFF_TABLE_SQL))

        else:

            constraints = {
                row[0]
                for row in conn.execute(
                    text(
                        "SELECT conname FROM pg_constraint "
                        "WHERE conrelid = 'doctor_day_offs'::regclass"
                    )
                )
            }

            if "uq_doctor_day_off" not in constraints:

                conn.execute(
                    text(
                        "ALTER TABLE doctor_day_offs ADD CONSTRAINT "
                        "uq_doctor_day_off UNIQUE (doctor_id, date)"
                    )
                )


_CLINIC_DAY_OFF_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS clinic_day_offs (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    reason VARCHAR(255),
    CONSTRAINT uq_clinic_day_off UNIQUE (date)
)
"""


def ensure_clinic_day_off_table():
    """Create the clinic_day_offs table and ensure the unique constraint.

    Safe to call on every startup:
    - CREATE TABLE IF NOT EXISTS is a no-op when the table already exists.
    - Adds the (date) unique constraint if missing so the clinic cannot
      have the same day off twice.
    - Drops the legacy clinic_id column (the app is single-clinic and
      day-offs are clinic-wide), keeping the table in sync with the model.
    """
    with engine.begin() as conn:

        if "clinic_day_offs" not in inspect(conn).get_table_names():

            conn.execute(text(_CLINIC_DAY_OFF_TABLE_SQL))

        else:

            columns = {
                column["name"]
                for column in inspect(conn).get_columns("clinic_day_offs")
            }

            if "clinic_id" in columns:

                conn.execute(
                    text(
                        "ALTER TABLE clinic_day_offs DROP COLUMN clinic_id"
                    )
                )

            constraints = {
                row[0]
                for row in conn.execute(
                    text(
                        "SELECT conname FROM pg_constraint "
                        "WHERE conrelid = 'clinic_day_offs'::regclass"
                    )
                )
            }

            if "uq_clinic_day_off" not in constraints:

                conn.execute(
                    text(
                        "ALTER TABLE clinic_day_offs ADD CONSTRAINT "
                        "uq_clinic_day_off UNIQUE (date)"
                    )
                )


if __name__ == "__main__":

    ensure_reminder_columns()

    ensure_clinic_table()

    ensure_single_clinic()

    ensure_doctor_clinic_assignment()

    ensure_doctor_schedule_table()

    ensure_doctor_day_off_table()

    ensure_clinic_day_off_table()

    print("Reminder columns ensured.")
    print("Clinic table ensured.")
    print("Clinic seed ensured.")
    print("Doctor clinic assignment ensured.")
    print("Doctor schedule table ensured.")
    print("Doctor day-off table ensured.")
    print("Clinic day-off table ensured.")