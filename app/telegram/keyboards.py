from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


def doctor_keyboard(doctors):

    keyboard = []

    for doctor in doctors:

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{doctor.name} ({doctor.specialization})",
                    callback_data=f"doctor:{doctor.name}",
                )
            ]
        )

    return InlineKeyboardMarkup(keyboard)


def slot_keyboard(slots):

    keyboard = []

    row = []

    for index, slot in enumerate(slots):

        row.append(
            InlineKeyboardButton(
                text=slot,
                callback_data=f"slot:{slot}",
            )
        )

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)