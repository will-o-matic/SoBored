from typing import Optional
from pydantic import BaseModel

class EventState(BaseModel):
    input_type: Optional[str] = None
    raw_input: Optional[str] = None
    source: Optional[str] = None  # "telegram", "web", etc.
