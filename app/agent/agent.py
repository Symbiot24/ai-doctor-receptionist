"""
Doctor Appointment Agent
Orchestrates the conversation flow using 21st AI for natural language understanding
and executes appropriate tools based on user intent.
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from app.agent.tools import (
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
    view_appointments,
    doctor_search,
    available_slots,
    general_chat
)

logger = logging.getLogger(__name__)

# Tool mapping: maps intent names to tool functions
TOOL_MAPPING = {
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "reschedule_appointment": reschedule_appointment,
    "view_appointments": view_appointments,
    "doctor_search": doctor_search,
    "available_slots": available_slots,
    "general_chat": general_chat
}

# Tool descriptions for the 21st AI to understand what each tool does
TOOL_DESCRIPTIONS = {
    "book_appointment": {
        "description": "Book a new appointment with a doctor",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_name": {"type": "string", "description": "Name of the doctor"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "Time in HH:MM format"},
                "patient_name": {"type": "string", "description": "Patient's full name"},
                "patient_phone": {"type": "string", "description": "Patient's phone number"}
            },
            "required": ["doctor_name", "date", "time", "patient_name", "patient_phone"]
        }
    },
    "cancel_appointment": {
        "description": "Cancel an existing appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer", "description": "ID of the appointment to cancel"},
                "patient_phone": {"type": "string", "description": "Patient's phone number for verification"}
            },
            "required": ["appointment_id", "patient_phone"]
        }
    },
    "reschedule_appointment": {
        "description": "Reschedule an existing appointment to a new date and/or time",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer", "description": "ID of the appointment to reschedule"},
                "patient_phone": {"type": "string", "description": "Patient's phone number for verification"},
                "new_date": {"type": "string", "description": "New date in YYYY-MM-DD format"},
                "new_time": {"type": "string", "description": "New time in HH:MM format"}
            },
            "required": ["appointment_id", "patient_phone", "new_date", "new_time"]
        }
    },
    "view_appointments": {
        "description": "View all appointments for a patient",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_phone": {"type": "string", "description": "Patient's phone number"}
            },
            "required": ["patient_phone"]
        }
    },
    "doctor_search": {
        "description": "Search for doctors by specialty or name",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string", "description": "Medical specialty to search for (e.g., cardiology, dermatology)"},
                "name": {"type": "string", "description": "Doctor's name to search for"}
            }
        }
    },
    "available_slots": {
        "description": "Get available appointment slots for a doctor on a specific date",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_name": {"type": "string", "description": "Name of the doctor"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"}
            },
            "required": ["doctor_name", "date"]
        }
    },
    "general_chat": {
        "description": "Handle general conversation and questions that don't require specific tools",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "User's message or question"}
            },
            "required": ["message"]
        }
    }
}

class DoctorAppointmentAgent:
    """
    Main agent class that orchestrates the conversation flow.
    Uses 21st AI for intent recognition and tool selection,
    then executes the appropriate tool function.
    """
    
    def __init__(self):
        """Initialize the agent."""
        self.system_prompt = self._build_system_prompt()
        logger.info("DoctorAppointmentAgent initialized")
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for the 21st AI.
        This prompt defines the agent's behavior and available tools.
        """
        tools_desc = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in TOOL_DESCRIPTIONS.items()
        ])
        
        return f"""You are a helpful doctor appointment booking assistant. 
Your goal is to help users book, cancel, reschedule, and view appointments with doctors.

You have access to the following tools:
{tools_desc}

When a user sends a message:
1. Analyze their intent and determine which tool (if any) is appropriate
2. Extract the necessary parameters from the user's message
3. Execute the tool with those parameters
4. Return the result in a helpful, conversational manner

Guidelines:
- Always be polite and helpful
- If you're missing required information, ask clarifying questions
- For appointment booking, you need: doctor name, date (YYYY-MM-DD), time (HH:MM), patient name, patient phone
- For cancellation/rescheduling, you need: appointment ID and patient phone
- For viewing appointments, you need: patient phone
- For doctor search, you can search by specialty or name
- For available slots, you need: doctor name and date (YYYY-MM-DD)
- If the user's request is unclear or doesn't match any tool, use general_chat
- Confirm important details before booking/canceling/rescheduling
- Format dates as YYYY-MM-DD and times as HH:MM (24-hour format)
- If a tool returns an error, explain it to the user and ask for clarification

Current date: {datetime.now().strftime('%Y-%m-%d')}
"""

    async def process_message(self, message: str) -> str:
        """
        Process a user message and return an appropriate response.
        
        Args:
            message: The user's input message
            
        Returns:
            A response string to send back to the user
        """
        try:
            # Use 21st AI to determine intent and extract parameters
            intent, params = await self._determine_intent(message)
            
            logger.info(f"Determined intent: {intent}, params: {params}")
            
            # Execute the appropriate tool
            if intent in TOOL_MAPPING:
                tool_func = TOOL_MAPPING[intent]
                result = tool_func(params)
                
                # Format the response based on the tool result
                return self._format_tool_response(intent, result)
            else:
                # Fallback to general chat
                result = general_chat({"message": message})
                return self._format_tool_response("general_chat", result)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return "I'm sorry, I encountered an error processing your request. Please try again."
    
    async def _determine_intent(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Use 21st AI to determine the user's intent and extract parameters.
        
        Args:
            message: The user's input message
            
        Returns:
            Tuple of (intent_name, parameters_dict)
        """
        try:
            # Use 21st AI to generate a response that includes the tool call
            # We'll use the 21st CLI to generate a structured response
            from kilo.utils.localhost import tunnel  # For localhost tunneling if needed
            
            # Prepare the prompt for 21st AI
            prompt = f"""{self.system_prompt}

User message: "{message}"

Based on the user's message, determine the appropriate intent and extract any necessary parameters.
Respond with a JSON object in the following format:
{{
  "intent": "intent_name",
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}

If the user's request doesn't match any specific intent or you need more information, use "general_chat" as the intent.
If you need to ask for clarification, you can include a "response" field in the parameters that should be shown to the user.
"""

            # Use 21st AI to generate the intent detection
            # We'll use the 21st CLI's generate function
            from app.agent.twenty_first import twenty_first_cli
            
            response = await twenty_first_cli.generate(
                prompt=prompt,
                mode="code",  # We want structured output
                variant_count=1
            )
            
            # Extract the JSON from the response
            # The 21st CLI returns a structured response with code
            # We need to parse the JSON from the response
            import json
            import re
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                intent = result.get("intent", "general_chat")
                parameters = result.get("parameters", {})
                return intent, parameters
            else:
                # Fallback to general chat if we can't parse JSON
                logger.warning("Could not parse JSON from 21st AI response")
                return "general_chat", {"message": message}
                
        except Exception as e:
            logger.error(f"Error determining intent with 21st AI: {e}", exc_info=True)
            # Fallback to general chat
            return "general_chat", {"message": message}
    
    def _format_tool_response(self, intent: str, result: Dict[str, Any]) -> str:
        """
        Format the tool result into a user-friendly response.
        
        Args:
            intent: The intent that was executed
            result: The result dictionary from the tool function
            
        Returns:
            A formatted response string
        """
        if not result.get("success", False):
            # Tool execution failed
            error_msg = result.get("message", "An unknown error occurred")
            return f"I'm sorry, but I encountered an issue: {error_msg}"
        
        # Format successful responses based on intent
        if intent == "book_appointment":
            msg = result.get("message", "Appointment booked successfully!")
            apt_id = result.get("appointment_id")
            if apt_id:
                msg += f" Your appointment ID is {apt_id}."
            return msg
            
        elif intent == "cancel_appointment":
            return result.get("message", "Appointment cancelled successfully.")
            
        elif intent == "reschedule_appointment":
            msg = result.get("message", "Appointment rescheduled successfully.")
            apt_id = result.get("appointment_id")
            if apt_id:
                msg += f" Your appointment ID is {apt_id}."
            return msg
            
        elif intent == "view_appointments":
            appointments = result.get("appointments", [])
            count = result.get("count", 0)
            
            if count == 0:
                return "You don't have any upcoming appointments."
            
            response = f"You have {count} upcoming appointment(s):\n\n"
            for apt in appointments:
                response += f"📅 {apt['date']} at {apt['time']}\n"
                response += f"👨‍⚕️ Dr. {apt['doctor_name']} ({apt['specialty']})\n"
                response += f"📋 Status: {apt['status']}\n"
                if apt.get('id'):
                    response += f"🆔 Appointment ID: {apt['id']}\n"
                response += "\n"
            
            return response.strip()
            
        elif intent == "doctor_search":
            doctors = result.get("doctors", [])
            count = result.get("count", 0)
            
            if count == 0:
                return "I couldn't find any doctors matching your criteria."
            
            elif count == 0:
                return "I couldn't find any doctors matching your criteria."
            
            response = f"I found {count} doctor(s) matching your criteria:\n\n"
            for doc in doctors:
                response += f"👨‍⚕️ Dr. {doc['name']}\n"
                response += f"🩺 Specialty: {doc['specialty']}\n"
                if doc.get('phone'):
                    response += f"📞 Phone: {doc['phone']}\n"
                if doc.get('email'):
                    response += f"📧 Email: {doc['email']}\n"
                response += "\n"
            
            return response.strip()
            
        elif intent == "available_slots":
            doctor_name = result.get("doctor_name", "the doctor")
            date = result.get("date", "")
            slots = result.get("available_slots", [])
            count = result.get("count", 0)
            
            if count == 0:
                return f"I'm sorry, but {doctor_name} doesn't have any available slots on {date}."
            
            response = f"Available slots for Dr. {doctor_name} on {date}:\n\n"
            for i, slot in enumerate(slots, 1):
                response += f"{i}. {slot}\n"
            
            response += "\nWould you like to book one of these slots?"
            return response.strip()
            
        elif intent == "general_chat":
            return result.get("message", "I'm here to help you with doctor appointments. How can I assist you today?")
            
        else:
            # Generic fallback
            return result.get("message", "I've processed your request. Is there anything else I can help you with?")

# Create a singleton instance
doctor_agent = DoctorAppointmentAgent()