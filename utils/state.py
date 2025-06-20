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
