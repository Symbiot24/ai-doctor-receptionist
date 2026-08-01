from app.agent.doctor_agent import DoctorAgent
from app.agent.prompts import SYSTEM_PROMPT
from app.memory.conversation import conversation_manager

agent = DoctorAgent()


def generate_reply(user_id: int, user_message: str):

    history = conversation_manager.get_messages(user_id)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
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