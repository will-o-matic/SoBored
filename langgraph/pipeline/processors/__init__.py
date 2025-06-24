"""
Specialized processors for different input types
"""

from .base_processor import BaseProcessor
from .url_processor import URLProcessor
from .text_processor import TextProcessor

__all__ = ["BaseProcessor", "URLProcessor", "TextProcessor"]