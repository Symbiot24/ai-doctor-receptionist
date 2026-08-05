"""
Tool Executor for the Doctor Appointment Agent.
Responsible for executing tools based on LLM decisions.
"""

from typing import Dict, Any
from app.agent.tools import (
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
    view_appointments,
    doctor_search,
    available_slots,
    general_chat
)

# Mapping of tool names to their functions
TOOL_MAP = {
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "reschedule_appointment": reschedule_appointment,
    "view_appointments": view_appointments,
    "doctor_search": doctor_search,
    "available_slots": available_slots,
    "general_chat": general_chat
}

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Dictionary containing the result of the tool execution
    """
    # Check if tool exists
    if tool_name not in TOOL_MAP:
        return {
            "success": False,
            "message": f"Unknown tool: {tool_name}. Please try again."
        }
    
    # Get the tool function
    tool_func = TOOL_MAP[tool_name]
    
    try:
        # Execute the tool
        result = tool_func(arguments)
        return result
    except Exception as e:
        # Log the error (in a real app, use proper logging)
        print(f"Error executing tool {tool_name}: {e}")
        return {
            "success": False,
            "message": "An internal error occurred while processing your request. Please try again."
        }