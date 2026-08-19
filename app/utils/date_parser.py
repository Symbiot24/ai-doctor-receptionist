"""Natural language date parsing helpers.

Understands free-text dates such as "tomorrow", "day after tomorrow",
"26 august", "August 26, 2026", "next monday", "in 3 days" and standard
YYYY-MM-DD / DD-MM-YYYY formats, resolving them to a concrete ``date``.
"""

import calendar
import re
from datetime import date
from datetime import datetime
from datetime import timedelta


class DateParseError(ValueError):
    """Raised when a date cannot be understood from the given text."""


MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

ORDINAL_SUFFIX = re.compile(r"(st|nd|rd|th)\b", re.IGNORECASE)

LEADING_FILLER = re.compile(
    r"^(on|for|the|at|by|of|this|a)\s+",
    re.IGNORECASE,
)


def add_months(base, months):
    """Add a number of calendar months, clamping the day to month end."""
    month = base.month - 1 + months
    year = base.year + month // 12
    month = month % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def format_date(value):
    """Format a date as e.g. '26 August 2026' for user-facing messages."""
    return f"{value.day} {value.strftime('%B %Y')}"


def _clean(text):
    text = re.sub(r"[.!?]+$", "", text.strip())
    text = re.sub(r"\s+", " ", text)
    while LEADING_FILLER.match(text):
        text = LEADING_FILLER.sub("", text)
    return text.strip().lower()


def _resolve_year(candidate, today):
    """If no year was given and the date already passed, roll to next year."""
    if candidate < today:
        candidate = candidate.replace(year=candidate.year + 1)
    return candidate


def _parse_relative(text, today):
    day_pattern = r"(\d{1,2})(?:st|nd|rd|th)?"
    month_word = "|".join(sorted(MONTHS, key=len, reverse=True))

    if text in ("today", "tonight"):
        return today
    if text in ("tomorrow", "tom", "tmr", "tmrw"):
        return today + timedelta(days=1)
    if text in ("day after tomorrow", "after tomorrow", "overmorrow"):
        return today + timedelta(days=2)
    if text in ("yesterday", "previous day"):
        return today - timedelta(days=1)

    # --- Next month on a specific day, e.g. "5th of next month" ---
    match = re.fullmatch(
        rf"{day_pattern}\s+(?:of\s+)?next\s+month",
        text,
    )
    if match:
        base = add_months(today, 1)
        return base.replace(day=int(match.group(1)))

    match = re.fullmatch(
        rf"next\s+month\s+(?:on\s+)?(?:the\s+)?{day_pattern}",
        text,
    )
    if match:
        base = add_months(today, 1)
        return base.replace(day=int(match.group(1)))

    # --- Relative day/week/month counts ---
    match = re.fullmatch(rf"in\s+{day_pattern}\s+days?", text)
    if match:
        return today + timedelta(days=int(match.group(1)))

    match = re.fullmatch(rf"after\s+{day_pattern}\s+days?", text)
    if match:
        return today + timedelta(days=int(match.group(1)))

    match = re.fullmatch(rf"{day_pattern}\s+days?\s+from\s+now", text)
    if match:
        return today + timedelta(days=int(match.group(1)))

    if text in ("in a day", "after a day", "next day"):
        return today + timedelta(days=1)
    if text in ("in a week", "after a week", "next week", "a week from now"):
        return today + timedelta(days=7)
    if text in ("in 2 weeks", "after 2 weeks", "two weeks from now", "in a fortnight"):
        return today + timedelta(days=14)
    if text in ("in a month", "after a month", "next month", "a month from now"):
        return add_months(today, 1)
    if text in ("in 3 weeks", "after 3 weeks", "three weeks from now"):
        return today + timedelta(days=21)

    # --- Weekdays ---
    weekday_match = re.fullmatch(
        rf"(next|this|coming)?\s*([a-z]+)",
        text,
    )
    if weekday_match:
        prefix, name = weekday_match.group(1), weekday_match.group(2)
        target = WEEKDAYS.get(name)
        if target is not None:
            if prefix == "this":
                allow_today = True
            else:
                allow_today = False
            days_ahead = (target - today.weekday()) % 7
            if days_ahead == 0 and not allow_today:
                days_ahead = 7
            return today + timedelta(days=days_ahead)

    # --- Day + month name, e.g. "26 august" or "26th of august 2026" ---
    match = re.fullmatch(
        rf"{day_pattern}\s+(?:of\s+)?({month_word})(?:[,\s]+(\d{{4}}))?",
        text,
    )
    if match:
        day = int(match.group(1))
        month = MONTHS[match.group(2)]
        year = int(match.group(3)) if match.group(3) else today.year
        return _resolve_year(date(year, month, day), today)

    # --- Month name + day, e.g. "august 26" or "Aug 26, 2026" ---
    match = re.fullmatch(
        rf"({month_word})\s+{day_pattern}(?:[,\s]+(\d{{4}}))?",
        text,
    )
    if match:
        month = MONTHS[match.group(1)]
        day = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else today.year
        return _resolve_year(date(year, month, day), today)

    return None


def parse_date(text, today=None):
    """Parse free-text or formatted date into a ``datetime.date``.

    Raises ``DateParseError`` when the input cannot be understood.
    """
    if text is None:
        raise DateParseError("Please provide a date.")
    today = today or date.today()
    cleaned = _clean(str(text))

    if not cleaned:
        raise DateParseError("Please provide a date.")

    numeric_formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%d %m %Y",
        "%d-%m-%y",
        "%d/%m/%y",
        "%m-%d-%Y",
    )

    for fmt in numeric_formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    resolved = _parse_relative(cleaned, today)
    if resolved is not None:
        return resolved

    raise DateParseError(
        f"Could not understand the date '{text}'. "
        "Try something like 'tomorrow', '26 August' or 'YYYY-MM-DD'."
    )