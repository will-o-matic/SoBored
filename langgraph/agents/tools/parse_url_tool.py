import json
import os
import re
from datetime import datetime
from langchain_core.tools import tool

try:
    import anthropic
except ImportError:
    anthropic = None

@tool
def parse_url_content(webpage_content: str, webpage_title: str = "Untitled") -> dict:
    """
    Parse webpage content using Claude API to extract event details.
    
    Args:
        webpage_content: Text content from webpage
        webpage_title: Title of the webpage
        
    Returns:
        Dict containing parsed event details from webpage
    """
    try:
        print(f"[PARSE] Content length: {len(webpage_content) if webpage_content else 0}, Title: {webpage_title}")
        if not webpage_content:
            print(f"[PARSE] No content provided")
            return {"parsing_confidence": 0.0, "error": "No webpage content provided"}
        
        # Check if anthropic is available
        if not anthropic:
            return _fallback_parse_webpage(webpage_content, webpage_title)
        
        # Get API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return _fallback_parse_webpage(webpage_content, webpage_title)
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Get current date for relative date processing (EST timezone)
        import pytz
        est = pytz.timezone('US/Eastern')
        current_date = datetime.now(est).strftime("%Y-%m-%d")
        current_day = datetime.now(est).strftime("%A")
        
        # Enhanced prompt for webpage event extraction
        prompt = f"""Extract event details from this webpage content and return ONLY a JSON object with these exact fields:

Current system date: {current_date} ({current_day})

You are analyzing content from a webpage. Look for:
- Event announcements, listings, or descriptions
- Concert/show listings
- Meetup or gathering information
- Workshop or class schedules
- Conference or seminar details
- Party or social event information

Page Title: {webpage_title}

Webpage Content:
{webpage_content[:3000]}

Return JSON with these fields (use null for missing information):
{{
  "title": "event name/title", 
  "date": "YYYY-MM-DD HH:MM format (convert relative dates to actual dates based on current system time)",
  "location": "venue/location",
  "description": "brief description", 
  "confidence": 0.8
}}

Set confidence between 0-1 based on:
- 0.9-1.0: Clear event with specific date/time/location
- 0.7-0.8: Event details present but some info missing
- 0.5-0.6: Possible event but unclear details
- 0.1-0.4: No clear event information

Return ONLY the JSON, no other text."""

        # Call Claude API (using Haiku for cost efficiency)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse the JSON response
        response_text = response.content[0].text.strip()
        
        try:
            parsed_data = json.loads(response_text)
            
            # Map to our return fields
            result = {
                "parsing_confidence": min(max(parsed_data.get("confidence", 0.5), 0.0), 1.0)
            }
            
            if parsed_data.get("title"):
                result["event_title"] = parsed_data["title"]
            if parsed_data.get("date") and parsed_data["date"] != "null":
                result["event_date"] = parsed_data["date"]
            if parsed_data.get("location"):
                result["event_location"] = parsed_data["location"]
            if parsed_data.get("description"):
                result["event_description"] = parsed_data["description"]
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: try to extract some basic info from webpage
            return _fallback_parse_webpage(webpage_content, webpage_title)
        
    except Exception as e:
        fallback_result = _fallback_parse_webpage(webpage_content, webpage_title)
        fallback_result["error"] = f"Claude API URL parsing failed: {str(e)}"
        return fallback_result


def _fallback_parse_webpage(content: str, title: str) -> dict:
    """Simple fallback parsing if Claude API fails."""
    result = {"parsing_confidence": 0.2}  # Lower confidence for regex fallback
    
    # Use page title as potential event title
    if title and title.lower() != "untitled":
        # Clean up title (remove site name, etc)
        clean_title = re.sub(r'\s*[-|•]\s*.*$', '', title).strip()
        if clean_title:
            result["event_title"] = clean_title[:100]
    
    # Look for date patterns in content
    date_patterns = [
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s*,?\s*\w+\s*\d{1,2}\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b(today|tomorrow|tonight)\b',
        r'\b\d{1,2}:\d{2}\s*(am|pm|AM|PM)\b'
    ]
    
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        dates_found.extend(matches)
    
    if dates_found:
        result["event_date"] = str(dates_found[0])
    
    # Look for location indicators
    location_patterns = [
        r'\b(?:at|@)\s+([A-Z][a-z\s]+(?:Hall|Center|Club|Bar|Cafe|Restaurant|Theatre|Theater|Venue))\b',
        r'\b\d+\s+[A-Z][a-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, content)
        if match:
            result["event_location"] = match.group(1) if pattern.startswith(r'\b(?:at|@)') else match.group(0)
            break
    
    # Use truncated content as description
    clean_content = re.sub(r'\s+', ' ', content).strip()
    result["event_description"] = clean_content[:200]
    
    return result