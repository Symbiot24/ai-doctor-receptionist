from datetime import datetime

from app.agent.doctor_agent import DoctorAgent
from app.agent.prompts import SYSTEM_PROMPT, DOCTORS_CONTEXT_PROMPT
from app.memory.conversation import conversation_manager
from app.database.db import SessionLocal
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService

agent = DoctorAgent()


def build_doctors_context() -> str:
    """Build a context block of doctors using REAL data from the database.

    Includes static doctor details (specialization, fee, working hours)
    plus today's actually available slots computed from the appointments table.
    """
    db = SessionLocal()
    try:
        doctor_service = DoctorService(db)
        slot_service = SlotService(db)
        doctors = doctor_service.get_all()

        today = datetime.now().date()

        lines = []

        for doctor in doctors:

            hours = doctor.working_hours or "N/A"

            slots = slot_service.available_slots(
                doctor.name,
                today,
            )

            slots_text = ", ".join(slots) if slots else "None"

            lines.append(
                f"- {doctor.name} | {doctor.specialization or 'N/A'} | "
                f"Consultation fee: ₹{doctor.consultation_fee or 'N/A'} | "
                f"Working hours: {hours} | "
                f"Available slots on {today}: {slots_text}"
            )
    finally:
        db.close()

    return "\n".join(lines) if lines else "No doctors are currently available."


def generate_reply(user_id: int, user_message: str):

    history = conversation_manager.get_messages(user_id)

    doctors_context = build_doctors_context()

    system_content = (
        SYSTEM_PROMPT
        + DOCTORS_CONTEXT_PROMPT.format(doctors=doctors_context)
    )

    messages = [
        {
            "role": "system",
            "content": system_content,
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    reply = agent.chat(messages)

    conversation_manager.add_message(
        user_id,
        "user",
        user_message,
    )

    conversation_manager.add_message(
        user_id,
        "assistant",
        reply,
    )

    return reply