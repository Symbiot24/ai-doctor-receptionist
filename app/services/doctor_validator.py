from datetime import datetime
from datetime import time


class DoctorValidator:

    SHIFT_PAIRS = [
        ("morning_start", "morning_end"),
        ("evening_start", "evening_end"),
    ]

    @staticmethod
    def _to_time(value):
        """Normalize a "HH:MM" string or a datetime.time into a time."""
        if value is None or isinstance(value, time):
            return value

        if isinstance(value, str):
            try:
                return datetime.strptime(value.strip(), "%H:%M").time()
            except ValueError:
                raise ValueError(
                    f"Invalid time value {value!r}. Use 'HH:MM'."
                )

        raise ValueError(
            f"Invalid time value {value!r}. Use 'HH:MM'."
        )

    @classmethod
    def validate(
        cls,
        data: dict,
        partial: bool = False,
    ) -> list:
        """Return a list of validation error strings (empty when valid).

        `partial=False` requires name and specialization.
        `partial=True` only checks fields that are present (for updates).
        """
        errors = []

        if (not partial) or "name" in data:
            name = data.get("name")
            if not name or not str(name).strip():
                errors.append("name is required")

        if (not partial) or "specialization" in data:
            specialization = data.get("specialization")
            if not specialization or not str(specialization).strip():
                errors.append("specialization is required")

        if "consultation_fee" in data and data.get("consultation_fee") is not None:
            fee = data["consultation_fee"]
            try:
                if int(fee) < 0:
                    errors.append("consultation_fee cannot be negative")
            except (TypeError, ValueError):
                errors.append("consultation_fee must be a number")

        for start_key, end_key in cls.SHIFT_PAIRS:

            if start_key not in data and end_key not in data:
                continue

            start_value = data.get(start_key)
            end_value = data.get(end_key)

            if start_value and end_value:

                try:
                    start_time = cls._to_time(start_value)
                    end_time = cls._to_time(end_value)
                except ValueError as error:
                    errors.append(str(error))
                    continue

                if end_time <= start_time:
                    errors.append(
                        f"{start_key}/{end_key} invalid: end must be after start"
                    )

        return errors