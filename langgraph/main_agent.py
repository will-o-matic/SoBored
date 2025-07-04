"""
Main entry point for the event processing system with smart pipeline integration.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .agents.event_agent import create_event_agent
from .agents.dry_run_agent import create_dry_run_event_agent
from .pipeline.smart_pipeline import should_use_smart_pipeline, process_with_smart_pipeline
from .observability.langsmith_config import configure_langsmith, log_agent_session_start, log_agent_session_end
from .observability.structured_logging import ReActAgentLogger

# Load environment variables
load_dotenv()

# Configure observability
configure_langsmith()
agent_logger = ReActAgentLogger()


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
    dry_run: bool = False,
    user_id: Optional[str] = None,
    telegram_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Process event input using smart pipeline or ReAct agent based on feature flags.
    
    Args:
        raw_input: Raw input content to process
        source: Source of the input (telegram, web, etc.)
        input_type: Pre-classified input type (optional, used by ReAct agent)
        dry_run: If True, use dry-run mode that doesn't save to Notion
        user_id: User ID from Telegram or other source (optional)
        telegram_data: Optional Telegram-specific data (for image downloads, etc.)
        
    Returns:
        Dict containing processing results
    """
    import time
    
    # Start session logging
    start_time = time.time()
    session_id = f"{source}_{user_id or 'anon'}_{int(start_time)}"
    
    log_agent_session_start(user_id=user_id, source=source)
    agent_logger.log_agent_invocation_start(
        user_id=user_id,
        source=source,
        raw_input=raw_input,
        session_id=session_id
    )
    
    try:
        # Feature flag: Check if smart pipeline should be used
        if should_use_smart_pipeline():
            print(f"[MAIN] Using SMART PIPELINE (dry_run={dry_run})")
            result = process_with_smart_pipeline(
                raw_input=raw_input,
                source=source,
                user_id=user_id,
                dry_run=dry_run,
                telegram_data=telegram_data
            )
            
            # Add session metadata for compatibility
            result["session_id"] = session_id
            result["processing_method"] = "smart_pipeline"
            
        else:
            # Fallback to ReAct agent
            print(f"[MAIN] Using REACT AGENT (dry_run={dry_run})")
            
            # Create the appropriate agent (regular or dry-run)
            if dry_run:
                print("[MAIN] Creating DRY-RUN agent processor")
                agent = create_dry_run_event_processor()
            else:
                print("[MAIN] Creating regular agent processor")
                agent = create_event_processor()
            
            # Process the input
            result = agent.process_event(raw_input, source, input_type, user_id)
            result["processing_method"] = "react_agent"
        
        # Log successful completion
        duration_ms = (time.time() - start_time) * 1000
        log_agent_session_end(user_id=user_id, source=source, success=True)
        agent_logger.log_agent_invocation_end(
            user_id=user_id,
            source=source,
            success=True,
            duration_ms=duration_ms,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        # Log error
        duration_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        
        log_agent_session_end(user_id=user_id, source=source, success=False, error=error_msg)
        agent_logger.log_agent_invocation_end(
            user_id=user_id,
            source=source,
            success=False,
            error=error_msg,
            duration_ms=duration_ms,
            session_id=session_id
        )
        
        return {
            "success": False,
            "error": error_msg,
            "raw_input": raw_input,
            "source": source,
            "session_id": session_id,
            "processing_method": "failed"
        }


# Main entry point for the system
app = create_event_processor()