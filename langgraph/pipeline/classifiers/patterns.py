"""
Pattern definitions for smart classification
"""

import re
from typing import Dict, List

# URL patterns for Tier 1 classification
URL_PATTERNS = {
    "http_https": re.compile(r'^https?://[^\s]+$', re.IGNORECASE),
    "www_domain": re.compile(r'^www\.[^\s]+\.[a-z]{2,}', re.IGNORECASE),
    "domain_only": re.compile(r'^[a-zA-Z0-9-]+\.[a-z]{2,}(/.*)?$'),
}

# Event-related text patterns
TEXT_PATTERNS = {
    "event_keywords": re.compile(
        r'\b(event|concert|show|performance|workshop|seminar|meeting|conference|'
        r'festival|party|gathering|class|lesson|tour|exhibition|presentation)\b',
        re.IGNORECASE
    ),
    "date_time": re.compile(
        r'\b(today|tomorrow|tonight|this\s+(weekend|week|month)|'
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)|'
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}|'
        r'\d{1,2}(am|pm|:\d{2}))\b',
        re.IGNORECASE
    ),
    "location_indicators": re.compile(
        r'\b(at|@|in|on|near|downtown|uptown|venue|location|address|street|ave|avenue|blvd|boulevard|rd|road)\b',
        re.IGNORECASE
    ),
}

# Email patterns
EMAIL_PATTERNS = {
    "email": re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    "email_in_text": re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'),
}

# Phone number patterns
PHONE_PATTERNS = {
    "us_phone": re.compile(r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'),
    "international": re.compile(r'^\+[1-9]\d{1,14}$'),
}

def get_classification_confidence(input_text: str, classification: str) -> float:
    """
    Calculate confidence score for classification based on pattern matches
    
    Args:
        input_text: Raw input text
        classification: Predicted classification
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    confidence = 0.0
    
    if classification == "url":
        # Check URL patterns
        if URL_PATTERNS["http_https"].match(input_text):
            confidence = 0.95
        elif URL_PATTERNS["www_domain"].match(input_text):
            confidence = 0.90
        elif URL_PATTERNS["domain_only"].match(input_text):
            confidence = 0.85
            
    elif classification == "text":
        # Count pattern matches for text
        matches = 0
        total_patterns = 3
        
        if TEXT_PATTERNS["event_keywords"].search(input_text):
            matches += 1
        if TEXT_PATTERNS["date_time"].search(input_text):
            matches += 1
        if TEXT_PATTERNS["location_indicators"].search(input_text):
            matches += 1
            
        confidence = 0.6 + (matches / total_patterns) * 0.3
        
    elif classification == "email":
        if EMAIL_PATTERNS["email"].match(input_text):
            confidence = 0.95
        elif EMAIL_PATTERNS["email_in_text"].search(input_text):
            confidence = 0.80
            
    return min(confidence, 1.0)