from typing import Optional
from pydantic import BaseModel, Field

class EventState(BaseModel):
    """State object for event classification pipeline."""
    
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
        description="Error message if classification fails"
    )
