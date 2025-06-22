from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class EventState(BaseModel):
    """State object for event classification and parsing pipeline."""
    
    input_type: Optional[str] = Field(
        default=None, 
        description="Classified input type: 'text', 'url', 'image', 'unknown', or 'error'"
    )
    raw_input: str = Field(
        description="Raw input content to be classified"
    )
    source: str = Field(
        description="Source of the input (e.g., 'telegram', 'web', 'email')"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if processing fails"
    )
    
    # Parsed event details
    event_title: Optional[str] = Field(
        default=None,
        description="Extracted event title/name"
    )
    event_date: Optional[str] = Field(
        default=None,
        description="Extracted event date/time"
    )
    event_location: Optional[str] = Field(
        default=None,
        description="Extracted event location/venue"
    )
    event_description: Optional[str] = Field(
        default=None,
        description="Extracted event description/details"
    )
    parsing_confidence: Optional[float] = Field(
        default=None,
        description="Confidence score for parsed event details (0-1)"
    )
    
    # Response handling
    response_message: Optional[str] = Field(
        default=None,
        description="Formatted response message for the user"
    )
    
    # Notion integration fields
    notion_page_id: Optional[str] = Field(
        default=None,
        description="ID of the created Notion page"
    )
    notion_save_status: Optional[str] = Field(
        default=None,
        description="Status of Notion save operation: 'success', 'failed', 'skipped'"
    )
    notion_error: Optional[str] = Field(
        default=None,
        description="Error message if Notion save fails"
    )
    notion_url: Optional[str] = Field(
        default=None,
        description="URL to the created Notion page"
    )
    
    # Webpage fetching fields
    webpage_content: Optional[str] = Field(
        default=None,
        description="Fetched and cleaned webpage content"
    )
    webpage_title: Optional[str] = Field(
        default=None,
        description="Title extracted from the webpage"
    )
    fetch_status: Optional[str] = Field(
        default=None,
        description="Status of webpage fetch operation: 'success', 'failed', 'skipped'"
    )
    fetch_error: Optional[str] = Field(
        default=None,
        description="Error message if webpage fetch fails"
    )
