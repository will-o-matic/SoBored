import os
import json
from typing import Dict, Any, Optional, Union
from langchain_core.tools import tool

@tool
def dry_run_save_to_notion(event_data: Union[dict, str]) -> dict:
    """
    Dry-run version of save_to_notion that shows what would be saved without actually committing to Notion.
    
    Args:
        event_data: Dictionary containing event information with fields:
                   input_type, raw_input, source, event_title, event_date, 
                   event_location, event_description, user_id (optional)
        
    Returns:
        Dict containing what would be saved to Notion (no actual API calls made)
    """
    print("[DRY-RUN SAVE] *** DRY-RUN MODE - NO ACTUAL NOTION API CALLS WILL BE MADE ***")
    try:
        print(f"[DRY-RUN] Event data type: {type(event_data)}")
        print(f"[DRY-RUN] Event data: {event_data}")
        
        # Handle both dict and string inputs for backward compatibility
        if isinstance(event_data, str):
            # Handle case where agent passes a string that looks like Python dict representation
            try:
                # First try to parse as JSON
                cleaned_event_data = event_data.replace('None', 'null').replace("'", '"')
                data = json.loads(cleaned_event_data)
                print(f"[DRY-RUN] Parsed JSON string to dict: {data}")
            except json.JSONDecodeError:
                # If JSON parsing fails, try to evaluate as Python literal
                try:
                    import ast
                    data = ast.literal_eval(event_data)
                    print(f"[DRY-RUN] Parsed Python literal to dict: {data}")
                except (ValueError, SyntaxError):
                    print(f"[DRY-RUN] Failed to parse as JSON or Python literal: {event_data[:200]}...")
                    return {
                        "notion_save_status": "dry_run_failed",
                        "notion_error": f"Could not parse event_data string as dict or JSON",
                        "dry_run": True
                    }
        elif isinstance(event_data, dict):
            data = event_data
            print(f"[DRY-RUN] Using dict input directly: {data}")
        else:
            return {
                "notion_save_status": "dry_run_failed",
                "notion_error": f"Invalid event_data type: {type(event_data)}. Expected dict or str.",
                "dry_run": True
            }
            
    except Exception as e:
        print(f"[DRY-RUN] Error processing event_data: {e}")
        return {
            "notion_save_status": "dry_run_failed",
            "notion_error": f"Error processing event_data: {str(e)}",
            "dry_run": True
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
    
    # Check if we would skip saving
    if input_type in ['unknown', 'error']:
        return {
            "notion_save_status": "dry_run_skipped",
            "reason": f"Would skip save for input_type: {input_type}",
            "dry_run": True
        }
    
    # Check database configuration
    database_id = os.environ.get("NOTION_DATABASE_ID")
    if not database_id:
        return {
            "notion_save_status": "dry_run_failed",
            "notion_error": "Database ID not configured (would fail in real save)",
            "dry_run": True
        }
    
    # Build the properties that would be sent to Notion
    properties = _build_notion_properties(
        input_type, raw_input, source, event_title, 
        event_date, event_location, event_description, user_id
    )
    
    # Generate what the Notion page would look like
    mock_page_id = "dry-run-page-id-12345"
    page_id_clean = mock_page_id.replace('-', '')
    notion_url = f"https://www.notion.so/{page_id_clean}"
    
    result = {
        "notion_save_status": "dry_run_success",
        "notion_page_id": mock_page_id,
        "notion_url": notion_url,
        "dry_run": True,
        "would_save_properties": properties,
        "database_id": database_id,
        "event_data": {
            "input_type": input_type,
            "raw_input": raw_input,
            "source": source,
            "event_title": event_title,
            "event_date": event_date,
            "event_location": event_location,
            "event_description": event_description,
            "user_id": user_id
        }
    }
    
    print("[DRY-RUN SAVE] *** COMPLETED DRY-RUN - NO DATA WAS ACTUALLY SAVED TO NOTION ***")
    return result


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
    Build Notion page properties from event data (same logic as real save_to_notion).
    
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
        Dictionary of Notion page properties that would be created
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
    import pytz
    
    est = pytz.timezone('US/Eastern')
    current_time = datetime.now(est).isoformat()
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