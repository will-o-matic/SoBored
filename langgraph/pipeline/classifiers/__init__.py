"""
Smart classification system with 3-tier approach:
1. Regex/heuristic (instant, 95% accuracy)
2. Simple ML classifier (fast, 99% accuracy)  
3. LLM classification (complex edge cases)
"""

from .smart_classifier import SmartClassifier
from .patterns import URL_PATTERNS, TEXT_PATTERNS, EMAIL_PATTERNS

__all__ = ["SmartClassifier", "URL_PATTERNS", "TEXT_PATTERNS", "EMAIL_PATTERNS"]