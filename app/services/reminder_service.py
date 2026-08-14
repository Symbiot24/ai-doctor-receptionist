"""
Reminder Service

Automatically sends Telegram reminders to patients before their
booked appointments ("24 hours before" and "1 hour before").

Reminders are only sent while the appointment status is BOOKED —
cancelled appointments are never reminded.
"""

import asyncio
import threading
import time
from datetime import datetime
from datetime import timedelta

from telegram import Bot

from app.core.config import TELEGRAM_BOT_TOKEN
from app.database.db import SessionLocal
from app.database.models import Appointment

REMINDER_INTERVAL_SECONDS = 60

# Firing windows (generous catch-up ranges so the reminder is sent
# even if the loop runs slightly off schedule).
REMINDER_24H_MIN = timedelta(hours=23, minutes=30)
REMINDER_24H_MAX = timedelta(hours=24, minutes=30)
REMINDER_1H_MIN = timedelta(minutes=30)
REMINDER_1H_MAX = timedelta(minutes=90)


class ReminderService:

    def __init__(self, db):

        self.db = db

    # ---------------- Query ---------------- #

    def due_reminders(self):
        """Return [(appointment, kind)] pairs that need a reminder now.

        Only BOOKED appointments are considered. kind is either
        "24h" or "1h".
        """
        now = datetime.now()

        appointments = (
            self.db.query(Appointment)
            .filter(Appointment.status == "BOOKED")
            .all()
        )

        due = []

        for appointment in appointments:

            if not appointment.telegram_id:
                continue

            appointment_datetime = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time,
            )

            remaining = appointment_datetime - now

            if remaining <= timedelta(0):
                continue

            if (
                not appointment.reminder_24h_sent
                and REMINDER_24H_MIN <= remaining <= REMINDER_24H_MAX
            ):
                due.append((appointment, "24h"))

            elif (
                not appointment.reminder_1h_sent
                and REMINDER_1H_MIN <= remaining <= REMINDER_1H_MAX
            ):
                due.append((appointment, "1h"))

        return due

    # ---------------- Messaging ---------------- #

    def build_message(self, appointment, kind):
        """Build the reminder text for a given appointment."""
        time_str = appointment.appointment_time.strftime("%H:%M")

        date_str = appointment.appointment_date.strftime(
            "%A, %d %B %Y"
        )

        if kind == "24h":
            return (
                "🔔 Reminder!\n\n"
                "You have an appointment TOMORROW:\n\n"
                f"🆔 Appointment ID: {appointment.id}\n"
                f"👨‍⚕️ Doctor: {appointment.doctor}\n"
                f"📅 Date: {date_str}\n"
                f"🕒 Time: {time_str}\n\n"
                "Please arrive a few minutes early."
            )

        return (
            "⏰ Reminder!\n\n"
            "Your appointment is coming up in about 1 hour:\n\n"
            f"🆔 Appointment ID: {appointment.id}\n"
            f"👨‍⚕️ Doctor: {appointment.doctor}\n"
            f"📅 Date: {date_str}\n"
            f"🕒 Time: {time_str}\n\n"
            "See you soon!"
        )

    # ---------------- Send ---------------- #

    def _mark_sent(self, appointment, kind):

        if kind == "24h":
            appointment.reminder_24h_sent = True

        else:
            appointment.reminder_1h_sent = True

    async def send_reminder(self, appointment, kind, bot):
        """Send a single reminder and mark it as sent (in DB)."""
        message = self.build_message(appointment, kind)

        await bot.send_message(
            chat_id=int(appointment.telegram_id),
            text=message,
        )

        self._mark_sent(appointment, kind)

        print(
            f"Reminder sent ({kind}) for appointment "
            f"#{appointment.id} -> {appointment.telegram_id}"
        )

    async def process_due(self, bot):
        """Send every currently-due reminder.

        A failed send is NOT marked as sent, so it is retried on the
        next loop run.
        """
        due = self.due_reminders()

        sent_any = False

        for appointment, kind in due:

            try:
                await self.send_reminder(appointment, kind, bot)
                sent_any = True

            except Exception as error:
                print(
                    f"Failed to send reminder for appointment "
                    f"#{appointment.id}: {error}"
                )

        if sent_any:
            self.db.commit()

        return len(due)


# ---------------- Background Runner ---------------- #


def reminder_loop():
    """Poll the DB every minute and fire due reminders.

    Runs in its own daemon thread alongside the Telegram bot.
    """
    while True:

        try:

            db = SessionLocal()

            try:

                service = ReminderService(db)

                async def _run():

                    # Fresh Bot per loop so it does not outlive the
                    # asyncio event loop it is bound to.
                    bot = Bot(token=TELEGRAM_BOT_TOKEN)

                    await service.process_due(bot)

                asyncio.run(_run())

            finally:

                db.close()

        except Exception as error:

            print(f"Reminder loop error: {error}")

        time.sleep(REMINDER_INTERVAL_SECONDS)


def start_reminder_loop() -> threading.Thread:
    """Start the reminder runner in a background daemon thread."""
    thread = threading.Thread(
        target=reminder_loop,
        daemon=True,
    )

    thread.start()

    return thread