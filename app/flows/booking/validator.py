import re
from datetime import date
from datetime import datetime

from app.utils.date_parser import DateParseError
from app.utils.date_parser import add_months
from app.utils.date_parser import format_date
from app.utils.date_parser import parse_date


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
    def parse_date(text: str):
        """Parse a date in natural language or standard formats.

        Returns ``(appointment_date, error)``. ``appointment_date`` is
        ``None`` and ``error`` is set when the input cannot be understood.
        """
        try:
            return parse_date(text), None
        except DateParseError as error:
            return None, f"❌ {error}"

    @staticmethod
    def validate_booking_window(appointment_date: date):
        """Enforce that bookings fall inside the allowed booking window.

        Rules:
        - The date must not be in the past.
        - The date must not exceed one month (calendar month) from today.
        """
        today = date.today()

        if appointment_date < today:
            return False, (
                "❌ Appointment date cannot be in the past.\n"
                "Please choose a date from today onwards."
            )

        max_date = add_months(today, 1)

        if appointment_date > max_date:
            return False, (
                "❌ Appointments can only be booked up to 1 month in advance.\n"
                f"You can book until {format_date(max_date)}.\n"
                "Please choose a date within the next month."
            )

        return True, None

    @staticmethod
    def parse_and_validate_date(text: str):
        """Parse and validate a user-provided date in one step.

        Returns ``(appointment_date, error)``. ``appointment_date`` is
        ``None`` and ``error`` is set when the date is invalid.
        """
        appointment_date, error = BookingValidator.parse_date(text)

        if error:
            return None, error

        valid, message = BookingValidator.validate_booking_window(
            appointment_date
        )

        if not valid:
            return None, message

        return appointment_date, None

    @staticmethod
    def validate_date(date: str):

        appointment_date, error = BookingValidator.parse_and_validate_date(
            date
        )

        if error:
            return False, error

        return True, None

    @staticmethod
    def validate_time(time: str):

        try:
            datetime.strptime(time, "%H:%M")
            return True, None

        except ValueError:
            return False, "❌Invalid Time format.\nTime format should be HH:MM (24-hour)."