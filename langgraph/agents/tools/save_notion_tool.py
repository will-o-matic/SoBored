import os
from typing import Dict, Any, Union
from langchain_core.tools import tool
from .notion_saver import NotionSaver

@tool
def save_to_notion(event_data: Union[dict, str]) -> dict:
    """
    Save event data to Notion database.
    
    This tool uses a unified NotionSaver class that supports both real and dry-run modes
    based on the DRY_RUN environment variable. This eliminates code duplication and
    provides a single source of truth for Notion save logic.
    
    Args:
        event_data: Dictionary containing event information with fields:
                   input_type, raw_input, source, event_title, event_date, 
                   event_location, event_description, user_id (optional)
        
    Returns:
        Dict containing save status and Notion page details
    """
    # Check for dry-run mode from environment
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    
    # Create NotionSaver instance with appropriate mode
    saver = NotionSaver(dry_run=dry_run)
    
    # Delegate to the unified saver
    return saver.save(event_data)

