import os
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from utils.notion_client import get_notion_client

@tool
def save_to_notion(event_data: str) -> dict:
    """
    Save event data to Notion database.
    
    Args:
        event_data: JSON string containing event information with fields:
                   input_type, raw_input, source, event_title, event_date, 
                   event_location, event_description, user_id (optional)
        
    Returns:
        Dict containing save status and Notion page details
    """
    import json
    
    try:
        print(f"[SAVE] Event data: {event_data[:200]}...")
        
        # Handle case where agent passes a string that looks like JSON but has Python None values
        cleaned_event_data = event_data.replace('None', 'null').replace("'", '"')
        
        # Parse the event data from JSON string
        data = json.loads(cleaned_event_data)
        print(f"[SAVE] Parsed data: {data}")
    except json.JSONDecodeError as e:
        print(f"[SAVE] JSON decode error: {e}")
        print(f"[SAVE] Attempted to parse: {cleaned_event_data}")
        return {
            "notion_save_status": "failed",
            "notion_error": f"Invalid JSON format in event_data: {str(e)}"
        }
    
    # Extract individual fields
    input_type = data.get("input_type", "unknown")
    raw_input = data.get("raw_input", "")
    source = data.get("source", "unknown")
    event_title = data.get("event_title")
    event_date = data.get("event_date")
    event_location = data.get("event_location")
    event_description = data.get("event_description")
    user_id = data.get("user_id")
    
    # Skip saving if input_type is unknown or error
    if input_type in ['unknown', 'error']:
        return {
            "notion_save_status": "skipped",
            "reason": f"Skipping save for input_type: {input_type}"
        }
    
    # Get database ID from environment
    database_id = os.environ.get("NOTION_DATABASE_ID")
    if not database_id:
        return {
            "notion_save_status": "failed",
            "notion_error": "Database ID not configured"
        }
    
    try:
        # Initialize Notion client
        notion_client = get_notion_client()
        
        # Build page properties based on available data
        properties = _build_notion_properties(
            input_type, raw_input, source, event_title, 
            event_date, event_location, event_description, user_id
        )
        
        # Create page in Notion database
        page = notion_client.create_page(database_id, properties)
        
        if page:
            # Construct Notion URL
            page_id_clean = page['id'].replace('-', '')
            notion_url = f"https://www.notion.so/{page_id_clean}"
            
            return {
                "notion_save_status": "success",
                "notion_page_id": page['id'],
                "notion_url": notion_url
            }
        else:
            return {
                "notion_save_status": "failed",
                "notion_error": "Failed to create page in Notion"
            }
            
    except Exception as e:
        return {
            "notion_save_status": "failed",
            "notion_error": str(e)
        }


def _build_notion_properties(
    input_type: str,
    raw_input: str, 
    source: str,
    event_title: Optional[str],
    event_date: Optional[str],
    event_location: Optional[str],
    event_description: Optional[str],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build Notion page properties from event data.
    
    Args:
        input_type: Type of input
        raw_input: Original raw input content
        source: Source of the input
        event_title: Event title
        event_date: Event date
        event_location: Event location
        event_description: Event description
        user_id: User ID from Telegram or other source
        
    Returns:
        Dictionary of Notion page properties
    """
    properties = {}
    
    # Title (required)
    title_text = event_title or _generate_fallback_title(input_type, raw_input, source)
    properties["Title"] = {
        "title": [
            {
                "type": "text",
                "text": {"content": title_text}
            }
        ]
    }
    
    # Date/Time
    if event_date:
        properties["Date/Time"] = {
            "date": {"start": event_date}
        }
    
    # Location
    if event_location:
        properties["Location"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": event_location}
                }
            ]
        }
    
    # Description
    description_text = event_description or raw_input
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
    if source:
        properties["Source"] = {
            "select": {"name": source}
        }
    
    # URL (if input is a URL)
    if input_type == 'url' and _is_valid_url(raw_input):
        properties["URL"] = {
            "url": raw_input
        }
    
    # Classification
    if input_type:
        properties["Classification"] = {
            "select": {"name": input_type}
        }
    
    # Status (default to 'new')
    properties["Status"] = {
        "select": {"name": "new"}
    }
    
    # UserId (from Telegram or other source)
    if user_id:
        properties["UserId"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": str(user_id)}
                }
            ]
        }
    
    # Added timestamp (current datetime when record is created)
    from datetime import datetime
    current_time = datetime.now().isoformat()
    properties["Added"] = {
        "date": {"start": current_time}
    }
    
    return properties


def _generate_fallback_title(input_type: str, raw_input: str, source: str) -> str:
    """
    Generate a fallback title when no event title is available.
    
    Args:
        input_type: Type of input
        raw_input: Original raw input content
        source: Source of the input
        
    Returns:
        Generated title string
    """
    if input_type == 'url':
        return f"URL: {raw_input[:50]}..."
    elif input_type == 'image':
        return f"Image from {source}"
    elif input_type == 'text':
        # Use first 50 characters of text as title
        return raw_input[:50] + ("..." if len(raw_input) > 50 else "")
    else:
        return f"{input_type.capitalize()} from {source}"


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