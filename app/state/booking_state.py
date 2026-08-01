from enum import Enum


class BookingState(str, Enum):

    IDLE = "idle"

    ASK_NAME = "ask_name"

    ASK_PHONE = "ask_phone"

    ASK_AGE = "ask_age"

    ASK_GENDER = "ask_gender"

    ASK_SYMPTOMS = "ask_symptoms"

    ASK_DOCTOR = "ask_doctor"

    ASK_DATE = "ask_date"

    ASK_TIME = "ask_time"

    CONFIRM = "confirm"

    COMPLETE = "complete"