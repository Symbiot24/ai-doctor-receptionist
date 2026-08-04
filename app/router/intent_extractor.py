import json

from app.agent.doctor_agent import agent


class IntentExtractor:

    @staticmethod
    def extract(user_message: str):
        try:
            raw = agent.extract_intent(user_message)
            result = json.loads(raw)
            
            # Validate and normalize the result
            intent = result.get("intent", "UNKNOWN")
            entities = result.get("entities", {})
            
            # Ensure intent is one of the expected values
            valid_intents = [
                "BOOK_APPOINTMENT",
                "VIEW_APPOINTMENTS", 
                "CANCEL_APPOINTMENT",
                "RESCHEDULE_APPOINTMENT",
                "GENERAL_QUERY"
            ]
            if intent not in valid_intents:
                intent = "UNKNOWN"
            
            return {
                "intent": intent,
                "entities": entities,
            }
        except Exception:
            # Fallback for any error (Groq failure, JSON parse error, etc.)
            return {
                "intent": "UNKNOWN",
                "entities": {},
            }

        