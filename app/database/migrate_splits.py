"""Migrate the doctors table to split morning/evening shifts.

Adds morning_start / morning_end / evening_start / evening_end TIME
columns, sets realistic shift timings for the existing doctors, and
drops the old single start_time / end_time columns.
"""

from sqlalchemy import inspect
from sqlalchemy import text

from app.database.db import engine


# Realistic per-doctor split shifts: (morning_start, morning_end, evening_start, evening_end)
DOCTOR_SHIFTS = {
    "Dr Sharma": ("10:00", "14:00", "16:00", "19:00"),
    "Dr Mehta": ("09:30", "13:30", "17:00", "20:00"),
    "Dr Khan": ("11:00", "15:00", "16:30", "19:30"),
    "Dr Batra": ("10:00", "14:00", "17:00", "21:00"),
}

NEW_COLUMNS = {
    "morning_start": "TIME",
    "morning_end": "TIME",
    "evening_start": "TIME",
    "evening_end": "TIME",
}

OLD_COLUMNS = ["start_time", "end_time"]


def migrate():

    with engine.begin() as conn:

        inspector = inspect(conn)

        columns = [
            column["name"]
            for column in inspector.get_columns("doctors")
        ]

        # ---------- Add the new shift columns ----------
        for column, column_type in NEW_COLUMNS.items():

            if column not in columns:

                conn.execute(
                    text(
                        f"ALTER TABLE doctors ADD COLUMN {column} {column_type}"
                    )
                )

        # ---------- Backfill realistic shift timings ----------
        for name, shifts in DOCTOR_SHIFTS.items():

            conn.execute(
                text(
                    """
                    UPDATE doctors
                    SET morning_start = :morning_start,
                        morning_end = :morning_end,
                        evening_start = :evening_start,
                        evening_end = :evening_end
                    WHERE name = :name
                    """
                ),
                {
                    "name": name,
                    "morning_start": shifts[0],
                    "morning_end": shifts[1],
                    "evening_start": shifts[2],
                    "evening_end": shifts[3],
                },
            )

        # ---------- Drop the old columns ----------
        for old_column in OLD_COLUMNS:

            if old_column in columns:

                conn.execute(
                    text(
                        f"ALTER TABLE doctors DROP COLUMN {old_column}"
                    )
                )


if __name__ == "__main__":

    migrate()

    print("✔ Split shift migration completed.")