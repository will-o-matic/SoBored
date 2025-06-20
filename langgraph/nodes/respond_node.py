from typing import Dict, Any
from utils.state import EventState

def respond_to_user(state: EventState) -> Dict[str, Any]:
    """
    Generate a formatted response message for the user based on parsed event details.
    
    Args:
        state: Current EventState with parsed event information
        
    Returns:
        Dict containing the response message
    """
    try:
        confidence = state.parsing_confidence or 0.0
        
        # Handle error states
        if state.error:
            return {"response_message": "Sorry, I encountered an error processing your message. Please try again."}
        
        # Handle non-text inputs
        if state.input_type != "text":
            if state.input_type == "url":
                return {"response_message": "I see you shared a URL! I'm not set up to process links yet, but I'll learn soon."}
            elif state.input_type == "image":
                return {"response_message": "Nice image! I can't process images for events yet, but that feature is coming."}
            else:
                return {"response_message": "I'm not sure how to process that type of content yet."}
        
        # Handle low confidence parsing
        if confidence < 0.3:
            return {"response_message": "I couldn't find clear event details in your message. Try including things like event name, date, and location!"}
        
        # Build response based on what we found
        response_parts = []
        
        if confidence >= 0.7:
            response_parts.append("Great! I found event details:")
        else:
            response_parts.append("I think I found some event details:")
        
        # Add parsed details
        if state.event_title:
            response_parts.append(f"📅 **{state.event_title}**")
        
        details = []
        if state.event_date:
            details.append(f"🗓️ {state.event_date}")
        if state.event_location:
            details.append(f"📍 {state.event_location}")
        
        if details:
            response_parts.append(" | ".join(details))
        
        # Add confidence indicator for lower confidence scores
        if confidence < 0.7:
            response_parts.append(f"\n(Confidence: {confidence:.1%} - please double-check these details!)")
        
        # Add next steps hint
        response_parts.append("\n💡 Next: I'll save this to your Notion database soon!")
        
        response_message = "\n".join(response_parts)
        return {"response_message": response_message}
        
    except Exception as e:
        return {"response_message": f"Error generating response: {str(e)}"}