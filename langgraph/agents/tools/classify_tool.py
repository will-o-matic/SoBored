import re
from langchain_core.tools import tool

@tool
def classify_input(raw_input: str) -> dict:
    """
    Classify input content type (text, url, image, unknown, or error).
    
    Args:
        raw_input: Raw input content to be classified
        
    Returns:
        Dict containing classification results
    """
    try:
        print(f"[CLASSIFY] Input: {raw_input[:100]}...")
        content = raw_input or ""
        
        # Simple classification logic
        if re.search(r'https?://\S+', content):
            classification = "url"
        elif content.strip():
            classification = "text"
        else:
            classification = "unknown"
        
        result = {
            "input_type": classification,
            "raw_input": raw_input
        }
        print(f"[CLASSIFY] Result: {classification}")
        return result
        
    except Exception as e:
        print(f"[CLASSIFY] Error: {e}")
        return {
            "input_type": "error", 
            "error": str(e),
            "raw_input": raw_input
        }