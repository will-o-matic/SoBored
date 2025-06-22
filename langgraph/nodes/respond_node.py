from typing import Dict, Any
from utils.state import EventState

def respond_to_user(state: EventState) -> EventState:
    """
    Generate a formatted response message for the user based on parsed event details.
    
    Args:
        state: Current EventState with parsed event information
        
    Returns:
        Updated EventState with response message
    """
    try:
        confidence = state.parsing_confidence or 0.0
        
        # Handle error states
        if state.error:
            state.response_message = "Sorry, I encountered an error processing your message. Please try again."
            return state
        
        # Handle non-text inputs
        if state.input_type != "text":
            response_message = ""
            if state.input_type == "url":
                response_message = "I see you shared a URL!"
            elif state.input_type == "image":
                response_message = "Nice image! I've captured it for processing."
            else:
                response_message = "I've captured your content for processing."
            
            # Add Notion save status
            if state.notion_save_status == "success":
                response_message += f" ✅ Saved to Notion: {state.notion_url}"
            elif state.notion_save_status == "failed":
                response_message += f" ❌ Failed to save to Notion: {state.notion_error}"
            elif state.notion_save_status == "skipped":
                response_message += " (Skipped saving to Notion)"
            
            state.response_message = response_message
            return state
        
        # Handle low confidence parsing
        if confidence < 0.3:
            response_message = "I couldn't find clear event details in your message. Try including things like event name, date, and location!"
            
            # Add Notion save status even for low confidence
            if state.notion_save_status == "success":
                response_message += f" ✅ Saved to Notion anyway: {state.notion_url}"
            elif state.notion_save_status == "failed":
                response_message += f" ❌ Failed to save to Notion: {state.notion_error}"
            
            state.response_message = response_message
            return state
        
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
        
        # Add Notion save status
        if state.notion_save_status == "success":
            response_parts.append(f"\n✅ Saved to Notion: {state.notion_url}")
        elif state.notion_save_status == "failed":
            response_parts.append(f"\n❌ Failed to save to Notion: {state.notion_error}")
        elif state.notion_save_status == "skipped":
            response_parts.append("\n⏭️ Skipped saving to Notion")
        
        state.response_message = "\n".join(response_parts)
        return state
        
    except Exception as e:
        state.response_message = f"Error generating response: {str(e)}"
        return state