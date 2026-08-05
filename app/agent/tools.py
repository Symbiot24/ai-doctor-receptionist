"""
Tool implementations for the Doctor Appointment Bot.
Each tool is a thin wrapper around existing services.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, time
import logging

from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService
from app.flows.booking.flow import BookingFlow
from app.database.db import SessionLocal

logger = logging.getLogger(__name__)

# Initialize services
booking_flow = BookingFlow()


def book_appointment(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Book an appointment for a patient with a doctor.
    
    Args:
        arguments: Dictionary containing:
            - doctor_name (str): Name of the doctor
            - date (str): Date in YYYY-MM-DD format
            - time (str): Time in HH:MM format
            - patient_name (str): Name of the patient
            - patient_phone (str): Phone number of the patient
            
    Returns:
        Dictionary with booking result
    """
    try:
        doctor_name = arguments.get("doctor_name")
        date_str = arguments.get("date")
        time_str = arguments.get("time")
        patient_name = arguments.get("patient_name")
        patient_phone = arguments.get("patient_phone")
        
        if not all([doctor_name, date_str, time_str, patient_name, patient_phone]):
            return {
                "success": False,
                "message": "Missing required parameters: doctor_name, date, time, patient_name, patient_phone"
            }
        
        # Parse date and time
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        appointment_time = datetime.strptime(time_str, "%H:%M").time()
        
        # Use booking flow to book appointment
        result = booking_flow.book_appointment(
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            patient_name=patient_name,
            patient_phone=patient_phone
        )
        
        return {
            "success": True,
            "message": result.get("message", "Appointment booked successfully"),
            "appointment_id": result.get("appointment_id")
        }
        
    except ValueError as e:
        logger.error(f"Invalid date/time format: {e}")
        return {
            "success": False,
            "message": "Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM for time."
        }
    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        return {
            "success": False,
            "message": "Failed to book appointment. Please try again."
        }


def cancel_appointment(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cancel an existing appointment.
    
    Args:
        arguments: Dictionary containing:
            - appointment_id (int): ID of the appointment to cancel
            - patient_phone (str): Phone number of the patient (for verification)
            
    Returns:
        Dictionary with cancellation result
    """
    db = SessionLocal()
    try:
        appointment_id = arguments.get("appointment_id")
        patient_phone = arguments.get("patient_phone")
        
        if appointment_id is None or not patient_phone:
            return {
                "success": False,
                "message": "Missing required parameters: appointment_id and patient_phone"
            }
        
        # Use appointment service to cancel appointment
        appointment_service = AppointmentService(db)
        result = appointment_service.cancel_appointment(
            appointment_id=int(appointment_id),
            patient_phone=patient_phone
        )
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Appointment cancelled successfully")
        }
        
    except ValueError as e:
        logger.error(f"Invalid appointment ID: {e}")
        return {
            "success": False,
            "message": "Invalid appointment ID. Please provide a valid number."
        }
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        return {
            "success": False,
            "message": "Failed to cancel appointment. Please try again."
        }
    finally:
        db.close()


def reschedule_appointment(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reschedule an existing appointment.
    
    Args:
        arguments: Dictionary containing:
            - appointment_id (int): ID of the appointment to reschedule
            - patient_phone (str): Phone number of the patient (for verification)
            - new_date (str): New date in YYYY-MM-DD format
            - new_time (str): New time in HH:MM format
            
    Returns:
        Dictionary with rescheduling result
    """
    try:
        appointment_id = arguments.get("appointment_id")
        patient_phone = arguments.get("patient_phone")
        new_date_str = arguments.get("new_date")
        new_time_str = arguments.get("new_time")
        
        if appointment_id is None or not patient_phone or not new_date_str or not new_time_str:
            return {
                "success": False,
                "message": "Missing required parameters: appointment_id, patient_phone, new_date, new_time"
            }
        
        # Parse date and time
        new_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
        new_time = datetime.strptime(new_time_str, "%H:%M").time()
        
        # Use booking flow to reschedule appointment
        result = booking_flow.reschedule_appointment(
            appointment_id=int(appointment_id),
            patient_phone=patient_phone,
            new_date=new_date,
            new_time=new_time
        )
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Appointment rescheduled successfully"),
            "appointment_id": result.get("appointment_id")
        }
        
    except ValueError as e:
        logger.error(f"Invalid date/time format: {e}")
        return {
            "success": False,
            "message": "Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM for time."
        }
    except Exception as e:
        logger.error(f"Error rescheduling appointment: {e}")
        return {
            "success": False,
            "message": "Failed to reschedule appointment. Please try again."
        }


def view_appointments(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    View appointments for a patient.
    
    Args:
        arguments: Dictionary containing:
            - patient_phone (str): Phone number of the patient
            
    Returns:
        Dictionary with list of appointments
    """
    db = SessionLocal()
    try:
        patient_phone = arguments.get("patient_phone")
        
        if not patient_phone:
            return {
                "success": False,
                "message": "Missing required parameter: patient_phone"
            }
        
        # Use appointment service to get appointments
        appointment_service = AppointmentService(db)
        appointments = appointment_service.get_appointments_by_patient(patient_phone)
        
        # Format appointments for response
        formatted_appointments = []
        for appt in appointments:
            formatted_appointments.append({
                "id": appt.id,
                "doctor_name": appt.doctor.name if appt.doctor else "Unknown",
                "date": appt.appointment_date.strftime("%Y-%m-%d") if appt.appointment_date else "",
                "time": appt.appointment_time.strftime("%H:%M") if appt.appointment_time else "",
                "status": appt.status
            })
        
        # Create a user-friendly message
        if len(formatted_appointments) == 0:
            message = "You don't have any upcoming appointments."
        elif len(formatted_appointments) == 1:
            appt = formatted_appointments[0]
            message = f"You have one upcoming appointment:\n\n" \
                     f"ðŸ“… Date: {appt['date']}\n" \
                     f"ðŸ•’ Time: {appt['time']}\n" \
                     f"ðŸ‘¨â€âš•ï¸ Doctor: {appt['doctor_name']}\n" \
                     f"ðŸ“Œ Status: {appt['status']}"
        else:
            message = f"You have {len(formatted_appointments)} upcoming appointments:\n\n"
            for i, appt in enumerate(formatted_appointments, 1):
                message += f"{i}. ðŸ“… {appt['date']} at {appt['time']} with Dr. {appt['doctor_name']} ({appt['status']})\n"
        
        return {
            "success": True,
            "appointments": formatted_appointments,
            "count": len(formatted_appointments),
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}")
        return {
            "success": False,
            "message": "Failed to retrieve appointments. Please try again."
        }
    finally:
        db.close()


def doctor_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for doctors by specialty or name.
    
    Args:
        arguments: Dictionary containing:
            - specialty (str, optional): Medical specialty to search for
            - name (str, optional): Doctor's name to search for
            
    Returns:
        Dictionary with list of matching doctors
    """
    db = SessionLocal()
    try:
        specialty = arguments.get("specialty")
        name = arguments.get("name")
        
        if not specialty and not name:
            return {
                "success": False,
                "message": "Please provide either specialty or name to search for doctors"
            }
        
        # Use doctor service to search doctors
        doctor_service = DoctorService(db)
        if specialty:
            doctors = doctor_service.get_doctors_by_specialty(specialty)
        elif name:
            doctors = doctor_service.search_doctors_by_name(name)
        else:
            # This shouldn't happen due to above check, but just in case
            doctors = doctor_service.get_all_doctors()
        
        # Format doctors for response
        formatted_doctors = []
        for doctor in doctors:
            formatted_doctors.append({
                "id": doctor.id,
                "name": doctor.name,
                "specialty": doctor.specialty,
                "phone": doctor.phone,
                "email": doctor.email
            })
        
        # Create a user-friendly message
        if len(formatted_doctors) == 0:
            message = "I couldn't find any doctors matching your criteria."
        elif len(formatted_doctors) == 1:
            doc = formatted_doctors[0]
            message = f"I found one doctor matching your criteria:\n\n" \
                     f"ðŸ‘¨â€âš•ï¸ Name: {doc['name']}\n" \
                     f"ðŸ©º Specialty: {doc['specialty']}\n" \
                     f"ðŸ“ž Phone: {doc.get('phone', 'N/A')}\n" \
                     f"ðŸ“§ Email: {doc.get('email', 'N/A')}"
        else:
            message = f"I found {len(formatted_doctors)} doctors matching your criteria:\n\n"
            for i, doc in enumerate(formatted_doctors, 1):
                message += f"{i}. ðŸ‘¨â€âš•ï¸ {doc['name']} - {doc['specialty']}\n"
            message += "\nWould you like more details about any of these doctors?"
        
        return {
            "success": True,
            "doctors": formatted_doctors,
            "count": len(formatted_doctors),
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error searching doctors: {e}")
        return {
            "success": False,
            "message": "Failed to search for doctors. Please try again."
        }
    finally:
        db.close()


def available_slots(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get available appointment slots for a doctor on a specific date.
    
    Args:
        arguments: Dictionary containing:
            - doctor_name (str): Name of the doctor
            - date (str): Date in YYYY-MM-DD format
            
    Returns:
        Dictionary with available time slots
    """
    try:
        doctor_name = arguments.get("doctor_name")
        date_str = arguments.get("date")
        
        if not doctor_name or not date_str:
            return {
                "success": False,
                "message": "Missing required parameters: doctor_name and date"
            }
        
        # Parse date
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Use booking flow to get available slots
        slots = booking_flow.get_available_slots(
            doctor_name=doctor_name,
            appointment_date=appointment_date
        )
        
        # Format slots for response
        formatted_slots = [slot.strftime("%H:%M") for slot in slots]
        
        # Create a user-friendly message
        if len(formatted_slots) == 0:
            message = f"I'm sorry, but {doctor_name} doesn't have any available slots on {date_str}."
        else:
            message = f"Available slots for Dr. {doctor_name} on {date_str}:\n\n"
            for i, slot in enumerate(formatted_slots, 1):
                message += f"{i}. {slot}\n"
            message += "\nWould you like to book one of these slots?"
        
        return {
            "success": True,
            "doctor_name": doctor_name,
            "date": date_str,
            "available_slots": formatted_slots,
            "count": len(formatted_slots),
            "message": message
        }
        
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return {
            "success": False,
            "message": "Invalid date format. Please use YYYY-MM-DD."
        }
    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        return {
            "success": False,
            "message": "Failed to retrieve available slots. Please try again."
        }


def general_chat(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle general chat/conversation that doesn't require specific tool use.
    
    Args:
        arguments: Dictionary containing:
            - message (str): The user's message
            
    Returns:
        Dictionary with response message
    """
    try:
        message = arguments.get("message", "")
        
        if not message:
            return {
                "success": False,
                "message": "I didn't receive a message. How can I help you?"
            }
        
        # For now, we'll return a generic response
        # In a more sophisticated implementation, this could use the LLM directly
        # or a separate chat service
        return {
            "success": True,
            "message": "I'm here to help you with doctor appointments! You can ask me to book, cancel, reschedule, or view appointments, or search for doctors. How can I assist you today?"
        }
        
    except Exception as e:
        logger.error(f"Error in general chat: {e}")
        return {
            "success": False,
            "message": "I'm having trouble processing your request. Please try again."
        }