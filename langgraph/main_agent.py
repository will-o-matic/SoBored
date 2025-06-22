"""
Main entry point for the new ReAct agent-based event processing system.
This replaces the old StateGraph approach with proper ReAct agents and tools.
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
    
    This is the main entry point that replaces the old StateGraph invoke() method.
    
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


# Backward compatibility function for existing code
def create_main_graph():
    """
    Backward compatibility function.
    
    Returns the agent processor in a way that mimics the old graph.compile() interface.
    """
    class AgentWrapper:
        def __init__(self):
            self.agent = create_event_processor()
        
        def invoke(self, state_or_input):
            """
            Invoke method that mimics the old StateGraph interface.
            
            Args:
                state_or_input: Either an EventState object or raw input
                
            Returns:
                Processing results
            """
            # Handle EventState object (backward compatibility)
            if hasattr(state_or_input, 'raw_input'):
                return process_event_input(
                    raw_input=state_or_input.raw_input,
                    source=getattr(state_or_input, 'source', 'unknown'),
                    input_type=getattr(state_or_input, 'input_type', None)
                )
            
            # Handle direct string input
            elif isinstance(state_or_input, str):
                return process_event_input(raw_input=state_or_input)
            
            # Handle dict input
            elif isinstance(state_or_input, dict):
                return process_event_input(
                    raw_input=state_or_input.get('raw_input', ''),
                    source=state_or_input.get('source', 'unknown'),
                    input_type=state_or_input.get('input_type')
                )
            
            else:
                raise ValueError(f"Unsupported input type: {type(state_or_input)}")
    
    return AgentWrapper()


# Main entry point for the new system
app = create_event_processor()