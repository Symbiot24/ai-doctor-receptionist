from groq import Groq

from app.core.config import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)


class DoctorAgent:

    def __init__(self):
        self.client = client
        self.model = "llama-3.3-70b-versatile"

    def chat(self, messages):

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
        )

        return response.choices[0].message.content

    def invoke(self, prompt: str):

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI intent extraction engine. "
                        "Always return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )

        return response.choices[0].message.content

    def extract_intent(self, user_message: str) -> str:
        """Extract intent and entities from user message using LLM.
        
        Returns raw JSON string.
        """
        system_prompt = """You are an AI intent extraction engine.

Return ONLY valid JSON.

Schema:

{
  "intent": "",
  "entities": {}
}

Available intents:

BOOK_APPOINTMENT
VIEW_APPOINTMENTS
CANCEL_APPOINTMENT
RESCHEDULE_APPOINTMENT
GENERAL_QUERY

Extract any entities if present.

Possible entities:
- patient_name
- phone
- age
- gender
- doctor
- appointment_date
- appointment_time
- symptoms
- appointment_id

Examples:

User:
Book appointment with Dr Sharma tomorrow at 5 pm. My name is Rahul and I'm 22.

Output:
{
    "intent":"BOOK_APPOINTMENT",
    "entities":{
        "patient_name":"Rahul",
        "doctor":"Dr Sharma",
        "appointment_date":"2026-08-05",
        "appointment_time":"17:00",
        "age":22
    }
}

User:
Cancel my appointment

Output:
{
    "intent":"CANCEL_APPOINTMENT",
    "entities":{}
}

User:
Show my appointments

Output:
{
    "intent":"VIEW_APPOINTMENTS",
    "entities":{}
}

User:
I have fever and headache

Output:
{
    "intent":"GENERAL_QUERY",
    "entities":{
        "symptoms":"fever and headache"
    }
}

User:
Move my appointment to Friday

Output:
{
    "intent":"RESCHEDULE_APPOINTMENT",
    "entities":{
        "appointment_date":"2026-08-09"
    }
}

Return ONLY JSON.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
            )
            return response.choices[0].message.content
        except Exception:
            # Re-raise so caller can handle the fallback
            raise


agent = DoctorAgent()