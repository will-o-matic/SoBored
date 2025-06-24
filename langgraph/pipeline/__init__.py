"""
Smart Event Processing Pipeline

Optimized pipeline for event extraction with enhanced performance
and LangSmith integration for continuous improvement.
"""

from .smart_pipeline import SmartEventPipeline
from .classifiers.smart_classifier import SmartClassifier
from .processors.base_processor import BaseProcessor
from .processors.url_processor import URLProcessor
from .processors.text_processor import TextProcessor

__all__ = [
    "SmartEventPipeline",
    "SmartClassifier", 
    "BaseProcessor",
    "URLProcessor",
    "TextProcessor"
]