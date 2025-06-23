"""
LangSmith configuration and utilities for observability.
"""

import os
from typing import Optional, Dict, Any
from functools import wraps


def configure_langsmith() -> bool:
    """
    Configure LangSmith tracing based on environment variables.
    
    Returns:
        bool: True if LangSmith is configured and enabled, False otherwise
    """
    # Check if LangSmith should be enabled
    langsmith_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    
    if not langsmith_enabled:
        print("[LANGSMITH] LangSmith tracing disabled (LANGSMITH_TRACING=false)")
        return False
    
    # Check for required LangSmith environment variables
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("[LANGSMITH] Warning: LANGSMITH_API_KEY not set, tracing disabled")
        return False
    
    # Set default project name if not specified
    project_name = os.getenv("LANGSMITH_PROJECT", "sobored-event-agent")
    os.environ["LANGSMITH_PROJECT"] = project_name
    
    # Set default endpoint if not specified
    if not os.getenv("LANGSMITH_ENDPOINT"):
        os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    
    print(f"[LANGSMITH] LangSmith tracing enabled for project: {project_name}")
    return True


def get_langsmith_client():
    """
    Get LangSmith client if available, otherwise return None.
    
    Returns:
        LangSmith client or None
    """
    try:
        from langsmith import Client
        
        api_key = os.getenv("LANGSMITH_API_KEY")
        if not api_key:
            return None
            
        return Client(
            api_key=api_key,
            api_url=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        )
    except ImportError:
        print("[LANGSMITH] Warning: langsmith package not installed")
        return None
    except Exception as e:
        print(f"[LANGSMITH] Failed to initialize client: {e}")
        return None


def with_langsmith_tracing(
    run_name: Optional[str] = None,
    run_type: str = "chain",
    project_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
):
    """
    Decorator to add LangSmith tracing to function calls.
    
    Args:
        run_name: Name for the traced run
        run_type: Type of run (chain, tool, etc.)
        project_name: Override project name
        metadata: Additional metadata to attach
        tags: Tags for the run
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not configure_langsmith():
                # If LangSmith is not configured, just run the function normally
                return func(*args, **kwargs)
            
            try:
                from langsmith import traceable
                
                # Create the traceable wrapper
                traced_func = traceable(
                    run_type=run_type,
                    name=run_name or func.__name__,
                    project_name=project_name,
                    metadata=metadata,
                    tags=tags
                )(func)
                
                # Execute the traced function
                return traced_func(*args, **kwargs)
                
            except ImportError:
                print(f"[LANGSMITH] Warning: langsmith not available for {func.__name__}")
                return func(*args, **kwargs)
            except Exception as e:
                print(f"[LANGSMITH] Tracing error for {func.__name__}: {e}")
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def create_langsmith_config() -> Dict[str, Any]:
    """
    Create LangSmith configuration dictionary for agent invocation.
    
    Returns:
        Configuration dict with callbacks if LangSmith is enabled
    """
    if not configure_langsmith():
        return {}
    
    try:
        from langsmith.run_helpers import get_current_run_tree
        from langsmith import LangChainTracer
        
        # Create LangChain tracer for compatibility
        tracer = LangChainTracer(
            project_name=os.getenv("LANGSMITH_PROJECT", "sobored-event-agent")
        )
        
        return {
            "callbacks": [tracer],
            "tags": ["react-agent", "event-processing"]
        }
        
    except ImportError:
        print("[LANGSMITH] Warning: langsmith package not available")
        return {}
    except Exception as e:
        print(f"[LANGSMITH] Configuration error: {e}")
        return {}


def log_agent_session_start(user_id: Optional[str] = None, source: str = "unknown"):
    """
    Log the start of an agent processing session.
    
    Args:
        user_id: User ID if available
        source: Source of the input (telegram, web, etc.)
    """
    client = get_langsmith_client()
    if not client:
        return
    
    try:
        # Log session metadata
        metadata = {
            "event_type": "session_start",
            "user_id": user_id,
            "source": source,
            "agent_type": "react_event_processor"
        }
        
        # This would be used in combination with traced function calls
        print(f"[LANGSMITH] Session started - User: {user_id}, Source: {source}")
        
    except Exception as e:
        print(f"[LANGSMITH] Session logging error: {e}")


def log_agent_session_end(
    user_id: Optional[str] = None, 
    source: str = "unknown",
    success: bool = True,
    error: Optional[str] = None
):
    """
    Log the end of an agent processing session.
    
    Args:
        user_id: User ID if available
        source: Source of the input
        success: Whether the session completed successfully
        error: Error message if failed
    """
    client = get_langsmith_client()
    if not client:
        return
    
    try:
        metadata = {
            "event_type": "session_end",
            "user_id": user_id,
            "source": source,
            "success": success,
            "error": error if not success else None
        }
        
        status = "SUCCESS" if success else "ERROR"
        print(f"[LANGSMITH] Session ended - Status: {status}, User: {user_id}")
        
    except Exception as e:
        print(f"[LANGSMITH] Session end logging error: {e}")