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


if __name__ == "__main__":

    ensure_reminder_columns()

    ensure_clinic_table()

    ensure_single_clinic()

    print("✔ Reminder columns ensured.")
    print("✔ Clinic table ensured.")
    print("✔ Clinic seed ensured.")