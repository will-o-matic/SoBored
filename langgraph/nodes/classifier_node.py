import re
from typing import Dict, Any
from utils.state import EventState

def classify_input(state: EventState) -> Dict[str, Any]:
    """
    Classify input content and return state update.
    
    Args:
        state: Current EventState
        
    Returns:
        Dict containing state updates
    """
    try:
        content = state.raw_input or ""
        
        # Check for image separately (Telegram would pass metadata in the webhook)
        if state.input_type == "image":
            input_type = "image"
        elif re.search(r'https?://\S+', content):
            input_type = "url"
        elif content.strip():
            input_type = "text"
        else:
            input_type = "unknown"
        
        return {"input_type": input_type}
        
    except Exception as e:
        # Return error state update instead of raising
        return {"input_type": "error", "error": str(e)}
