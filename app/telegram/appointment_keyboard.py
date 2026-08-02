from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


def appointment_actions(appointment_id: int):

    keyboard = [
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"cancel:{appointment_id}",
            ),
            InlineKeyboardButton(
                "🔄 Reschedule",
                callback_data=f"reschedule:{appointment_id}",
            ),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)