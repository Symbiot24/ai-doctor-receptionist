import re
from datetime import datetime


class BookingValidator:

    @staticmethod
    def validate_name(name: str):
        if len(name.strip()) < 3:
            return False, "❌ Name must contain at least 3 characters."

        return True, None

    @staticmethod
    def validate_phone(phone: str):
        if not re.fullmatch(r"[6-9]\d{9}", phone):
            return False, "❌Invalid phone number.\nPlease enter a valid 10-digit Indian mobile number."

        return True, None

    @staticmethod
    def validate_age(age: str):
        try:
            age = int(age)

            if age < 1 or age > 120:
                return False, "❌ Age must be between 1 and 120."

            return True, None

        except ValueError:
            return False, "❌ Age must be a number."

    @staticmethod
    def validate_gender(gender: str):

        gender = gender.lower()

        if gender not in ["male", "female", "other"]:
            return False, "❌ Gender must be Male, Female or Other."

        return True, None

    @staticmethod
    def validate_date(date: str):

        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()

            if appointment_date < datetime.today().date():
                return False, "❌ Appointment date cannot be in the past."

            return True, None

        except ValueError:
            return False, "❌Invalid Date format.\nDate format should be YYYY-MM-DD."

    @staticmethod
    def validate_time(time: str):

        try:
            datetime.strptime(time, "%H:%M")
            return True, None

        except ValueError:
            return False, "❌Invalid Time format.\nTime format should be HH:MM (24-hour)."