from groq import Groq

from app.config import GROQ_API_KEY
from app.agent.prompts import SYSTEM_PROMPT

client = Groq(api_key=GROQ_API_KEY)


def ask_agent(message: str) -> str:

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    )

    return response.choices[0].message.content