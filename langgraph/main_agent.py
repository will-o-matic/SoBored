"""
Main entry point for the ReAct agent-based event processing system.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .agents.event_agent import create_event_agent

# Load environment variables
load_dotenv()


def create_event_processor() -> Any:
    """
    Create the main event processing agent.
    
    Returns:
        Configured event processing agent
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    return create_event_agent(api_key)


def process_event_input(
    raw_input: str,
    source: str = "unknown", 
    input_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process event input using the ReAct agent.
    
    Args:
        raw_input: Raw input content to process
        source: Source of the input (telegram, web, etc.)
        input_type: Pre-classified input type (optional)
        
    Returns:
        Dict containing processing results
    """
    try:
        # Create the agent
        agent = create_event_processor()
        
        # Process the input
        result = agent.process_event(raw_input, source, input_type)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_input": raw_input,
            "source": source
        }


# Main entry point for the system
app = create_event_processor()