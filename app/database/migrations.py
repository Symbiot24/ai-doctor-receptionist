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


if __name__ == "__main__":

    ensure_reminder_columns()

    print("✔ Reminder columns ensured.")