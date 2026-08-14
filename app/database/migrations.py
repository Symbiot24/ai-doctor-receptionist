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
    """Seed a default clinic record if the clinics table is empty.

    Safe to call on every startup (no-op when a clinic already exists).
    """
    with engine.begin() as conn:

        count = conn.execute(
            text("SELECT COUNT(*) FROM clinics")
        ).scalar()

        if count == 0:

            conn.execute(
                text(
                    "INSERT INTO clinics (name, description) VALUES "
                    "('My Clinic', 'Default clinic record')"
                )
            )


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
                    "SELECT id FROM clinics WHERE active = 'YES' "
                    "ORDER BY id LIMIT 1"
                )
            ).scalar()

            if clinic_id is None:

                clinic_id = conn.execute(
                    text("SELECT id FROM clinics ORDER BY id LIMIT 1")
                ).scalar()

            if clinic_id is not None:

                conn.execute(
                    text(
                        "UPDATE doctors SET clinic_id = :clinic_id "
                        "WHERE clinic_id IS NULL"
                    ),
                    {"clinic_id": clinic_id},
                )


if __name__ == "__main__":

    ensure_reminder_columns()

    ensure_clinic_table()

    ensure_single_clinic()

    ensure_doctor_clinic_assignment()

    print("✔ Reminder columns ensured.")
    print("✔ Clinic table ensured.")
    print("✔ Clinic seed ensured.")
    print("✔ Doctor clinic assignment ensured.")