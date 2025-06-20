import json
import os
from typing import Dict, Any
from utils.state import EventState

try:
    import anthropic
except ImportError:
    anthropic = None

def parse_text(state: EventState) -> Dict[str, Any]:
    """
    Parse text content using Claude API to extract event details.
    
    Args:
        state: Current EventState with classified text
        
    Returns:
        Dict containing parsed event details
    """
    try:
        if state.input_type != "text" or not state.raw_input:
            return {"parsing_confidence": 0.0}
        
        # Check if anthropic is available
        if not anthropic:
            return {"error": "anthropic library not installed", "parsing_confidence": 0.0}
        
        # Get API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not set", "parsing_confidence": 0.0}
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Structured prompt for event extraction
        prompt = f"""Extract event details from this text and return ONLY a JSON object with these exact fields:

Text: "{state.raw_input}"

Return JSON with these fields (use null for missing information):
{{
  "title": "event name/title",
  "date": "date/time information", 
  "location": "venue/location",
  "description": "brief description",
  "confidence": 0.8
}}

Set confidence between 0-1 based on how clear the event details are. Return ONLY the JSON, no other text."""

        # Call Claude API (using Haiku for cost efficiency)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse the JSON response
        response_text = response.content[0].text.strip()
        print(response_text)
        try:
            parsed_data = json.loads(response_text)
            
            # Map to our state fields
            updates = {}
            if parsed_data.get("title"):
                updates["event_title"] = parsed_data["title"]
            if parsed_data.get("date"):
                updates["event_date"] = parsed_data["date"]
            if parsed_data.get("location"):
                updates["event_location"] = parsed_data["location"]
            if parsed_data.get("description"):
                updates["event_description"] = parsed_data["description"]
            
            # Use Claude's confidence or calculate our own
            confidence = parsed_data.get("confidence", 0.5)
            updates["parsing_confidence"] = min(max(confidence, 0.0), 1.0)
            
            return updates
            
        except json.JSONDecodeError:
            # Fallback: try to extract some basic info
            return _fallback_parse(state.raw_input)
        
    except Exception as e:
        return {"error": f"Claude API parsing failed: {str(e)}", "parsing_confidence": 0.0}


def _fallback_parse(text: str) -> Dict[str, Any]:
    """Simple fallback parsing if Claude API fails."""
    import re
    
    updates = {"parsing_confidence": 0.3}  # Lower confidence for regex fallback
    
    # Extract first sentence as potential title
    title_match = re.search(r'^([^.!?]{10,60})', text)
    if title_match:
        updates["event_title"] = title_match.group(1).strip()
    
    # Look for basic date patterns
    date_patterns = [
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        r'\b(today|tomorrow|tonight)\b',
        r'\b\d{1,2}[/-]\d{1,2}\b'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            updates["event_date"] = match.group(0)
            break
    
    # Use full text as description
    updates["event_description"] = text[:200]  # Truncate if too long
    
    return updates