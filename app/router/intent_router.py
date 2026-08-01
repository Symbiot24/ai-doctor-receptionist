from enum import Enum


class Intent(str, Enum):
    BOOK = "book"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    GENERAL = "general"


class IntentRouter:

    BOOK_KEYWORDS = [
        "book",
        "appointment",
        "schedule",
        "consult",
        "doctor",
    ]

    CANCEL_KEYWORDS = [
        "cancel",
        "remove",
    ]

    RESCHEDULE_KEYWORDS = [
        "reschedule",
        "change",
        "shift",
    ]

    @staticmethod
    def detect(message: str) -> Intent:

        text = message.lower()

        if any(word in text for word in IntentRouter.CANCEL_KEYWORDS):
            return Intent.CANCEL

        if any(word in text for word in IntentRouter.RESCHEDULE_KEYWORDS):
            return Intent.RESCHEDULE

        if any(word in text for word in IntentRouter.BOOK_KEYWORDS):
            return Intent.BOOK

        return Intent.GENERAL