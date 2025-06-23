"""
Main entry point for the ReAct agent-based event processing system.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .agents.event_agent import create_event_agent
from .agents.dry_run_agent import create_dry_run_event_agent

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


def create_dry_run_event_processor() -> Any:
    """
    Create the dry-run event processing agent.
    
    Returns:
        Configured dry-run event processing agent
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    return create_dry_run_event_agent(api_key)


def process_event_input(
    raw_input: str,
    source: str = "unknown", 
    input_type: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Process event input using the ReAct agent.
    
    Args:
        raw_input: Raw input content to process
        source: Source of the input (telegram, web, etc.)
        input_type: Pre-classified input type (optional)
        dry_run: If True, use dry-run agent that doesn't save to Notion
        
    Returns:
        Dict containing processing results
    """
    try:
        # Create the appropriate agent (regular or dry-run)
        if dry_run:
            print("[MAIN] Creating DRY-RUN agent processor")
            agent = create_dry_run_event_processor()
        else:
            print("[MAIN] Creating regular agent processor")
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