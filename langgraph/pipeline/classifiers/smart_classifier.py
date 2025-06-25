"""
Smart 3-tier classification system for input content
"""

import logging
from typing import Dict, Optional
from .patterns import URL_PATTERNS, TEXT_PATTERNS, EMAIL_PATTERNS, get_classification_confidence

logger = logging.getLogger(__name__)

class SmartClassifier:
    """
    Three-tier classification system:
    1. Regex/heuristic 
    2. Simple ML classifier - TODO: Future implementation
    3. LLM classification
    """
    
    def __init__(self, use_llm_fallback: bool = True):
        self.use_llm_fallback = use_llm_fallback
        self.classification_stats = {
            "tier1_hits": 0,
            "tier2_hits": 0, 
            "tier3_hits": 0,
            "total_classifications": 0
        }
    
    def classify(self, raw_input: str) -> Dict[str, any]:
        """
        Classify input using 3-tier approach
        
        Args:
            raw_input: Raw input content to classify
            
        Returns:
            Dict containing classification results with confidence score
        """
        self.classification_stats["total_classifications"] += 1
        
        # Tier 1: Regex/Heuristic Classification (Instant)
        tier1_result = self._tier1_classify(raw_input)
        if tier1_result["confidence"] >= 0.85:
            self.classification_stats["tier1_hits"] += 1
            logger.debug(f"Tier 1 classification: {tier1_result}")
            return tier1_result
        
        # Tier 2: Simple ML Classifier (Future implementation)
        # tier2_result = self._tier2_classify(raw_input)
        # if tier2_result["confidence"] >= 0.90:
        #     self.classification_stats["tier2_hits"] += 1
        #     return tier2_result
        
        # Tier 3: LLM Classification (Complex cases)
        if self.use_llm_fallback:
            tier3_result = self._tier3_classify(raw_input)
            self.classification_stats["tier3_hits"] += 1
            logger.debug(f"Tier 3 LLM classification: {tier3_result}")
            return tier3_result
        else:
            # Return best guess from Tier 1 if no LLM fallback
            return tier1_result
    
    def _tier1_classify(self, raw_input: str) -> Dict[str, any]:
        """Regex/heuristic based classification"""
        raw_input = raw_input.strip()
        
        # Check for URLs first (most common case)
        if self._is_url(raw_input):
            classification = "url"
            confidence = get_classification_confidence(raw_input, "url")
            return {
                "input_type": classification,
                "raw_input": raw_input,
                "confidence": confidence,
                "method": "tier1_regex",
                "reasoning": "URL pattern detected"
            }
        
        # Check for email
        if self._is_email(raw_input):
            classification = "email"
            confidence = get_classification_confidence(raw_input, "email")
            return {
                "input_type": classification,
                "raw_input": raw_input,
                "confidence": confidence,
                "method": "tier1_regex", 
                "reasoning": "Email pattern detected"
            }
        
        # Check for event-related text
        if self._is_event_text(raw_input):
            classification = "text"
            confidence = get_classification_confidence(raw_input, "text")
            return {
                "input_type": classification,
                "raw_input": raw_input,
                "confidence": confidence,
                "method": "tier1_regex",
                "reasoning": "Event keywords and patterns detected"
            }
        
        # Default to text with low confidence
        return {
            "input_type": "text",
            "raw_input": raw_input,
            "confidence": 0.5,
            "method": "tier1_default",
            "reasoning": "No clear pattern detected, defaulting to text"
        }
    
    def _tier2_classify(self, raw_input: str) -> Dict[str, any]:
        """Simple ML classifier (Future implementation)"""
        # TODO: Implement lightweight ML model for edge cases
        # Could use simple features like:
        # - Length, word count, special character ratios
        # - Common event vocabulary presence
        # - Sentence structure patterns
        
        return {
            "input_type": "unknown",
            "raw_input": raw_input,
            "confidence": 0.0,
            "method": "tier2_ml",
            "reasoning": "ML classifier not yet implemented"
        }
    
    def _tier3_classify(self, raw_input: str) -> Dict[str, any]:
        """LLM-based classification for complex cases"""
        try:
            # Import existing classify_input tool
            from langgraph.agents.tools.classify_tool import classify_input
            
            # Use existing LLM classification as fallback
            result = classify_input(raw_input)
            
            # Enhance result with additional metadata
            enhanced_result = {
                **result,
                "confidence": 0.75,  # Default LLM confidence
                "method": "tier3_llm",
                "reasoning": "Complex case requiring LLM analysis"
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Tier 3 LLM classification failed: {e}")
            return {
                "input_type": "unknown",
                "raw_input": raw_input,
                "confidence": 0.3,
                "method": "tier3_error",
                "reasoning": f"LLM classification failed: {str(e)}"
            }
    
    def _is_url(self, text: str) -> bool:
        """Check if text is a URL"""
        return (URL_PATTERNS["http_https"].match(text) or 
                URL_PATTERNS["www_domain"].match(text) or
                URL_PATTERNS["domain_only"].match(text))
    
    def _is_email(self, text: str) -> bool:
        """Check if text is an email"""
        return (EMAIL_PATTERNS["email"].match(text) or
                EMAIL_PATTERNS["email_in_text"].search(text))
    
    def _is_event_text(self, text: str) -> bool:
        """Check if text contains event-related patterns"""
        has_event_keywords = TEXT_PATTERNS["event_keywords"].search(text)
        has_date_time = TEXT_PATTERNS["date_time"].search(text)
        has_location = TEXT_PATTERNS["location_indicators"].search(text)
        
        # Require at least 2 out of 3 pattern types for high confidence
        pattern_count = sum([bool(has_event_keywords), bool(has_date_time), bool(has_location)])
        return pattern_count >= 2
    
    def get_stats(self) -> Dict[str, any]:
        """Get classification statistics"""
        total = self.classification_stats["total_classifications"]
        if total == 0:
            return {"message": "No classifications performed yet"}
            
        return {
            "total_classifications": total,
            "tier1_percentage": (self.classification_stats["tier1_hits"] / total) * 100,
            "tier2_percentage": (self.classification_stats["tier2_hits"] / total) * 100,
            "tier3_percentage": (self.classification_stats["tier3_hits"] / total) * 100,
            "tier1_efficiency": self.classification_stats["tier1_hits"],
            "llm_usage": self.classification_stats["tier3_hits"]
        }