"""
21st CLI Interface for Doctor Appointment Agent
Handles communication with the 21st AI service for intent recognition and tool selection.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
try:
    from kilo.utils.localhost import tunnel
except ImportError:
    # Fallback for environments where kilo is not installed
    tunnel = None

logger = logging.getLogger(__name__)

class TwentyFirstCLI:
    """
    Wrapper for the 21st CLI (@21st-dev/cli) to generate structured responses
    for intent recognition and parameter extraction.
    """
    
    def __init__(self):
        """Initialize the 21st CLI wrapper."""
        logger.info("TwentyFirstCLI initialized")
    
    async def generate(
        self,
        prompt: str,
        mode: str = "code",
        variant_count: int = 1,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a response using the 21st AI via the 21st CLI.
        
        Args:
            prompt: The input prompt for the AI
            mode: Generation mode ('code' or 'sketch')
            variant_count: Number of variants to generate
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response from the AI
        """
        try:
            # In a real implementation, we would call the 21st CLI here
            # For now, we'll simulate the response since we don't have the actual CLI installed
            # In production, this would use: @21st-dev/cli generate ...
            
            logger.info(f"Generating response with 21st AI (mode={mode})")
            
            # Simulate a response for demonstration purposes
            # In reality, this would be an actual call to the 21st CLI
            simulated_response = await self._simulate_21st_response(prompt, mode)
            
            return simulated_response
            
        except Exception as e:
            logger.error(f"Error calling 21st CLI: {e}")
            # Return a fallback response
            return json.dumps({
                "intent": "general_chat",
                "parameters": {"message": "I'm having trouble processing that right now. Could you try again?"}
            })
    
    async def _simulate_21st_response(self, prompt: str, mode: str) -> str:
        """
        Simulate a response from the 21st AI for development purposes.
        In production, this would be replaced with actual CLI calls.
        
        Args:
            prompt: The input prompt
            mode: Generation mode
            
        Returns:
            Simulated JSON response
        """
        # Extract the user message from the prompt
        # The prompt contains: "User message: \"{message}\""
        import re
        user_message_match = re.search(r'User message: "([^"]*)"', prompt)
        user_message = user_message_match.group(1) if user_message_match else ""
        
        # Simple rule-based intent detection for simulation
        # In production, this would be done by the actual 21st AI
        intent, parameters = self._simulate_intent_detection(user_message)
        
        # Return as JSON string
        response = {
            "intent": intent,
            "parameters": parameters
        }
        
        return json.dumps(response, indent=2)
    
    def _simulate_intent_detection(self, message: str) -> tuple[str, dict]:
        """
        Simulate intent detection based on keywords.
        This is a placeholder for the actual 21st AI functionality.
        
        Args:
            message: The user's message
            
        Returns:
            Tuple of (intent, parameters)
        """
        message_lower = message.lower()
        
        # Booking intent
        if any(word in message_lower for word in ["book", "schedule", "appointment", "see doctor"]):
            # Try to extract parameters
            params = {}
            
            # Extract doctor name (simple pattern)
            doc_match = re.search(r'doctor\s+([a-zA-Z\s]+)', message_lower)
            if doc_match:
                params["doctor_name"] = doc_match.group(1).strip().title()
            
            # Extract date
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
                r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY
                r'(today|tomorrow|next week)'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, message_lower)
                if date_match:
                    date_str = date_match.group(1)
                    # Convert relative dates to actual dates (simplified)
                    if date_str == "today":
                        from datetime import datetime
                        params["date"] = datetime.now().strftime("%Y-%m-%d")
                    elif date_str == "tomorrow":
                        from datetime import datetime, timedelta
                        params["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    elif date_str == "next week":
                        from datetime import datetime, timedelta
                        params["date"] = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
                    else:
                        # Try to parse the date
                        try:
                            if '/' in date_str:
                                parts = date_str.split('/')
                                if len(parts) == 3:
                                    params["date"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                            elif '-' in date_str and len(date_str.split('-')[0]) == 4:
                                params["date"] = date_str  # Already YYYY-MM-DD
                            else:
                                parts = date_str.split('-')
                                if len(parts) == 3:
                                    params["date"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                        except:
                            pass
                    break
            
            # Extract time
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', message_lower)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                meridiem = time_match.group(3)
                
                if meridiem == "pm" and hour != 12:
                    hour += 12
                elif meridiem == "am" and hour == 12:
                    hour = 0
                
                params["time"] = f"{hour:02d}:{minute:02d}"
            
            # Extract patient name
            name_patterns = [
                r'patient\s+([a-zA-Z\s]+)',
                r'for\s+([a-zA-Z\s]+)',
                r'name\s+is\s+([a-zA-Z\s]+)'
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, message_lower)
                if name_match:
                    params["patient_name"] = name_match.group(1).strip().title()
                    break
            
            # Extract patient phone
            phone_match = re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[\-\s]??\d{4}|\d{3}[\-\s]??\d{4})', message)
            if phone_match:
                params["patient_phone"] = phone_match.group(0)
            
            # If we have enough parameters, assume booking intent
            if all(k in params for k in ["doctor_name", "date", "time", "patient_name", "patient_phone"]):
                return "book_appointment", params
            else:
                # Not enough info, ask for missing info
                return "general_chat", {
                    "message": "I'd be happy to help you book an appointment! I'll need a few more details:\n" +
                               "- Doctor's name\n" +
                               "- Date (YYYY-MM-DD format)\n" +
                               "- Time (HH:MM format, 24-hour)\n" +
                               "- Your full name\n" +
                               "- Your phone number\n\n" +
                               "Could you please provide these details?"
                }
        
        # Cancellation intent
        elif any(word in message_lower for word in ["cancel", "delete", "remove appointment"]):
            params = {}
            
            # Extract appointment ID
            id_match = re.search(r'appointment\s*#?(\d+)|id\s*#?(\d+)|#(\d+)', message_lower)
            if id_match:
                # Get the first non-None group
                id_val = next((x for x in id_match.groups() if x is not None), None)
                if id_val:
                    params["appointment_id"] = int(id_val)
            
            # Extract patient phone
            phone_match = re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[\-\s]??\d{4}|\d{3}[\-\s]??\d{4})', message)
            if phone_match:
                params["patient_phone"] = phone_match.group(0)
            
            if "appointment_id" in params and "patient_phone" in params:
                return "cancel_appointment", params
            else:
                return "general_chat", {
                    "message": "To cancel an appointment, I need:\n" +
                               "- Your appointment ID\n" +
                               "- Your phone number for verification\n\n" +
                               "Could you please provide both?"
                }
        
        # Reschedule intent
        elif any(word in message_lower for word in ["reschedule", "change appointment", "move appointment", "rebook"]):
            params = {}
            
            # Extract appointment ID
            id_match = re.search(r'appointment\s*#?(\d+)|id\s*#?(\d+)|#(\d+)', message_lower)
            if id_match:
                id_val = next((x for x in id_match.groups() if x is not None), None)
                if id_val:
                    params["appointment_id"] = int(id_val)
            
            # Extract patient phone
            phone_match = re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[\-\s]??\d{4}|\d{3}[\-\s]??\d{4})', message)
            if phone_match:
                params["patient_phone"] = phone_match.group(0)
            
            # Extract new date
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}-\d{1,2}-\d{4})',
                r'(today|tomorrow|next week)'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, message_lower)
                if date_match:
                    date_str = date_match.group(1)
                    if date_str == "today":
                        from datetime import datetime
                        params["new_date"] = datetime.now().strftime("%Y-%m-%d")
                    elif date_str == "tomorrow":
                        from datetime import datetime, timedelta
                        params["new_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    elif date_str == "next week":
                        from datetime import datetime, timedelta
                        params["new_date"] = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
                    else:
                        try:
                            if '/' in date_str:
                                parts = date_str.split('/')
                                if len(parts) == 3:
                                    params["new_date"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                            elif '-' in date_str and len(date_str.split('-')[0]) == 4:
                                params["new_date"] = date_str
                            else:
                                parts = date_str.split('-')
                                if len(parts) == 3:
                                    params["new_date"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                        except:
                            pass
                    break
            
            # Extract new time
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', message_lower)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                meridiem = time_match.group(3)
                
                if meridiem == "pm" and hour != 12:
                    hour += 12
                elif meridiem == "am" and hour == 12:
                    hour = 0
                
                params["new_time"] = f"{hour:02d}:{minute:02d}"
            
            if all(k in params for k in ["appointment_id", "patient_phone", "new_date", "new_time"]):
                return "reschedule_appointment", params
            else:
                missing = []
                if "appointment_id" not in params: missing.append("appointment ID")
                if "patient_phone" not in params: missing.append("phone number")
                if "new_date" not in params: missing.append("new date")
                if "new_time" not in params: missing.append("new time")
                
                return "general_chat", {
                    "message": f"To reschedule your appointment, I need the following information:\n" +
                               "- " + "\n- ".join(missing) +
                               "\n\nCould you please provide these details?"
                }
        
        # View appointments intent
        elif any(word in message_lower for word in ["view", "show", "list", "my appointments", "appointments"]):
            params = {}
            
            # Extract patient phone
            phone_match = re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[\-\s]??\d{4}|\d{3}[\-\s]??\d{4})', message)
            if phone_match:
                params["patient_phone"] = phone_match.group(0)
            
            if "patient_phone" in params:
                return "view_appointments", params
            else:
                return "general_chat", {
                    "message": "To view your appointments, I need your phone number for verification. Could you please provide it?"
                }
        
        # Doctor search intent
        elif any(word in message_lower for word in ["doctor", "find doctor", "search doctor", "look for doctor"]):
            params = {}
            
            # Extract specialty
            specialties = ["cardiology", "dermatology", "neurology", "orthopedics", "pediatrics", 
                         "psychiatry", "radiology", "surgery", "dentistry", "optometry"]
            for spec in specialties:
                if spec in message_lower:
                    params["specialty"] = spec.title()
                    break
            
            # Extract doctor name (look for patterns like "Dr. Smith" or "Doctor Smith")
            doc_name_match = re.search(r'dr\.?\s+([a-zA-Z\s]+)|doctor\s+([a-zA-Z\s]+)', message_lower)
            if doc_name_match:
                name = doc_name_match.group(1) or doc_name_match.group(2)
                if name:
                    params["name"] = name.strip().title()
            
            if params:
                return "doctor_search", params
            else:
                return "general_chat", {
                    "message": "I can help you find doctors by specialty or name. Are you looking for a particular specialty (like cardiology, dermatology, etc.) or do you have a specific doctor in mind?"
                }
        
        # Available slots intent
        elif any(word in message_lower for word in ["available", "slot", "availability", "free", "open"]):
            params = {}
            
            # Extract doctor name
            doc_name_match = re.search(r'dr\.?\s+([a-zA-Z\s]+)|doctor\s+([a-zA-Z\s]+)', message_lower)
            if doc_name_match:
                name = doc_name_match.group(1) or doc_name_match.group(2)
                if name:
                    params["doctor_name"] = name.strip().title()
            
            # Extract date
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}-\d{1,2}-\d{4})',
                r'(today|tomorrow|next week)'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, message_lower)
                if date_match:
                    date_str = date_match.group(1)
                    if date_str == "today":
                        from datetime import datetime
                        params["date"] = datetime.now().strftime("%Y-%m-%d")
                    elif date_str == "tomorrow":
                        from datetime import datetime, timedelta
                        params["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    elif date_str == "next week":
                        from datetime import datetime, timedelta
                        params["date"] = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
                    else:
                        try:
                            if '/' in date_str:
                                parts = date_str.split('/')
                                if len(parts) == 3:
                                    params["date"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                            elif '-' in date_str and len(date_str.split('-')[0]) == 4:
                                params["date"] = date_str
                            else:
                                parts = date_str.split('-')
                                if len(parts) == 3:
                                    params["date"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                        except:
                            pass
                    break
            
            if "doctor_name" in params and "date" in params:
                return "available_slots", params
            else:
                missing = []
                if "doctor_name" not in params: missing.append("doctor's name")
                if "date" not in params: missing.append("date")
                
                return "general_chat", {
                    "message": f"To check available slots, I need to know:\n" +
                               "- " + "\n- ".join(missing) +
                               "\n\nCould you please provide this information?"
                }
        
        # Default to general chat
        else:
            return "general_chat", {"message": message}

# Create a singleton instance
twenty_first_cli = TwentyFirstCLI()