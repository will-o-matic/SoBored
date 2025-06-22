"""
Save to Notion node for the event processing pipeline.
Saves classified and parsed events to a Notion database.
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from utils.state import EventState
from utils.notion_client import get_notion_client

logger = logging.getLogger(__name__)

def save_to_notion(state: EventState) -> EventState:
    """
    Save event data to Notion database.
    
    Args:
        state: EventState object containing classified and parsed data
        
    Returns:
        Updated EventState with Notion save results
    """
    logger.info(f"Processing Notion save for input_type: {state.input_type}")
    
    # Skip saving if input_type is unknown or error
    if state.input_type in ['unknown', 'error']:
        logger.info(f"Skipping Notion save for input_type: {state.input_type}")
        state.notion_save_status = 'skipped'
        return state
    
    # Get database ID from environment
    database_id = os.environ.get("NOTION_DATABASE_ID")
    if not database_id:
        logger.error("NOTION_DATABASE_ID environment variable not set")
        state.notion_save_status = 'failed'
        state.notion_error = "Database ID not configured"
        return state
    
    try:
        # Initialize Notion client
        notion_client = get_notion_client()
        
        # Build page properties based on available data
        properties = _build_notion_properties(state)
        
        # Create page in Notion database
        page = notion_client.create_page(database_id, properties)
        
        if page:
            state.notion_page_id = page['id']
            state.notion_save_status = 'success'
            # Construct Notion URL
            page_id_clean = page['id'].replace('-', '')
            state.notion_url = f"https://www.notion.so/{page_id_clean}"
            logger.info(f"Successfully saved to Notion: {state.notion_page_id}")
        else:
            state.notion_save_status = 'failed'
            state.notion_error = "Failed to create page in Notion"
            logger.error("Failed to create page in Notion database")
            
    except Exception as e:
        logger.error(f"Error saving to Notion: {str(e)}")
        state.notion_save_status = 'failed'
        state.notion_error = str(e)
    
    return state


def _build_notion_properties(state: EventState) -> Dict[str, Any]:
    """
    Build Notion page properties from EventState.
    
    Args:
        state: EventState containing event data
        
    Returns:
        Dictionary of Notion page properties
    """
    properties = {}
    
    # Title (required)
    title_text = state.event_title or _generate_fallback_title(state)
    properties["Title"] = {
        "title": [
            {
                "type": "text",
                "text": {"content": title_text}
            }
        ]
    }
    
    # Date/Time
    if state.event_date:
        properties["Date/Time"] = {
            "date": {"start": state.event_date}
        }
    
    # Location
    if state.event_location:
        properties["Location"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": state.event_location}
                }
            ]
        }
    
    # Description
    description_text = state.event_description or state.raw_input
    if description_text:
        properties["Description"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": description_text}
                }
            ]
        }
    
    # Source
    if state.source:
        properties["Source"] = {
            "select": {"name": state.source}
        }
    
    # URL (if input is a URL)
    if state.input_type == 'url' and _is_valid_url(state.raw_input):
        properties["URL"] = {
            "url": state.raw_input
        }
    
    # Classification
    if state.input_type:
        properties["Classification"] = {
            "select": {"name": state.input_type}
        }
    
    # Status (default to 'new')
    properties["Status"] = {
        "select": {"name": "new"}
    }
    
    return properties


def _generate_fallback_title(state: EventState) -> str:
    """
    Generate a fallback title when no event title is available.
    
    Args:
        state: EventState containing event data
        
    Returns:
        Generated title string
    """
    if state.input_type == 'url':
        return f"URL: {state.raw_input[:50]}..."
    elif state.input_type == 'image':
        return f"Image from {state.source}"
    elif state.input_type == 'text':
        # Use first 50 characters of text as title
        return state.raw_input[:50] + ("..." if len(state.raw_input) > 50 else "")
    else:
        return f"{state.input_type.capitalize()} from {state.source}"


def _is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL.
    
    Args:
        url: String to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        return url.startswith(('http://', 'https://'))
    except:
        return False