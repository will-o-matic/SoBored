"""
OCR tool for extracting text from images using Tesseract OCR.
"""

import io
import os
import requests
from PIL import Image
import tempfile
from typing import Dict, Any, Optional
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract not installed. OCR functionality will be limited.")

@tool
def extract_text_from_image(image_data: str, image_format: str = "auto") -> Dict[str, Any]:
    """
    Extract text from an image using OCR.
    
    Args:
        image_data: Image data as base64 string or file path or URL
        image_format: Image format (auto, base64, file, url)
        
    Returns:
        Dict containing OCR results with extracted text and confidence
    """
    if not OCR_AVAILABLE:
        return {
            "success": False,
            "error": "OCR library (pytesseract) not available",
            "extracted_text": "",
            "confidence": 0.0
        }
    
    try:
        print(f"[OCR] Processing image, format: {image_format}")
        
        # Load image based on format
        image = _load_image(image_data, image_format)
        if image is None:
            return {
                "success": False,
                "error": "Failed to load image",
                "extracted_text": "",
                "confidence": 0.0
            }
        
        # Preprocess image for better OCR
        processed_image = _preprocess_image(image)
        
        # Extract text using Tesseract
        extracted_text = pytesseract.image_to_string(processed_image, lang='eng')
        
        # Get confidence data
        confidence_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
        average_confidence = _calculate_average_confidence(confidence_data)
        
        # Clean up extracted text
        cleaned_text = _clean_extracted_text(extracted_text)
        
        print(f"[OCR] Extracted text length: {len(cleaned_text)}")
        print(f"[OCR] Average confidence: {average_confidence:.2f}")
        
        return {
            "success": True,
            "extracted_text": cleaned_text,
            "confidence": average_confidence,
            "raw_text": extracted_text,
            "word_count": len(cleaned_text.split()),
            "char_count": len(cleaned_text)
        }
        
    except Exception as e:
        error_msg = f"OCR processing failed: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "extracted_text": "",
            "confidence": 0.0
        }

def _load_image(image_data: str, image_format: str) -> Optional[Image.Image]:
    """Load image from different sources"""
    try:
        if image_format == "url" or (image_format == "auto" and image_data.startswith("http")):
            # Download image from URL
            response = requests.get(image_data, timeout=10)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
            
        elif image_format == "file" or (image_format == "auto" and os.path.exists(image_data)):
            # Load from file path
            return Image.open(image_data)
            
        elif image_format == "base64":
            # Load from base64 string
            import base64
            image_bytes = base64.b64decode(image_data)
            return Image.open(io.BytesIO(image_bytes))
            
        else:
            # Try to detect format automatically
            if image_data.startswith("http"):
                response = requests.get(image_data, timeout=10)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))
            elif os.path.exists(image_data):
                return Image.open(image_data)
            else:
                logger.error(f"Unknown image format: {image_format}")
                return None
                
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        return None

def _preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image for better OCR results"""
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image if it's too small (improves OCR accuracy)
        width, height = image.size
        min_dimension = 800
        
        if width < min_dimension or height < min_dimension:
            scale_factor = min_dimension / min(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
        
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}")
        return image

def _calculate_average_confidence(confidence_data: Dict) -> float:
    """Calculate average confidence from Tesseract confidence data"""
    try:
        confidences = [int(conf) for conf in confidence_data['conf'] if int(conf) > 0]
        if confidences:
            return sum(confidences) / len(confidences)
        return 0.0
    except Exception:
        return 0.0

def _clean_extracted_text(text: str) -> str:
    """Clean up extracted text by removing extra whitespace and fixing common OCR issues"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Fix common OCR character mistakes
    replacements = {
        '|': 'I',
        '0': 'O',  # In context where letters are expected
        '5': 'S',  # Common in event names
        '1': 'I',  # When clearly a letter
        '8': 'B',  # Sometimes confused
    }
    
    # Apply replacements cautiously (only when surrounded by letters)
    import re
    for old, new in replacements.items():
        # Only replace if surrounded by letters (likely a letter context)
        text = re.sub(rf'(?<=[a-zA-Z]){re.escape(old)}(?=[a-zA-Z])', new, text)
    
    # Remove isolated single characters that are likely OCR noise
    text = re.sub(r'\b[^\w\s]\b', '', text)
    
    # Clean up extra spaces
    text = ' '.join(text.split())
    
    return text.strip()

@tool
def validate_ocr_quality(ocr_result: Dict[str, Any], min_confidence: float = 70.0) -> Dict[str, Any]:
    """
    Validate OCR quality and determine if the extracted text is reliable.
    
    Args:
        ocr_result: Result from extract_text_from_image
        min_confidence: Minimum confidence threshold for reliability
        
    Returns:
        Dict with validation results
    """
    try:
        if not ocr_result.get("success", False):
            return {
                "is_reliable": False,
                "confidence": 0.0,
                "reason": "OCR extraction failed",
                "recommendation": "try_again"
            }
        
        confidence = ocr_result.get("confidence", 0.0)
        extracted_text = ocr_result.get("extracted_text", "")
        word_count = ocr_result.get("word_count", 0)
        
        # Check various quality indicators
        quality_checks = []
        
        # Confidence check
        if confidence >= min_confidence:
            quality_checks.append("high_confidence")
        elif confidence >= 50:
            quality_checks.append("medium_confidence")
        else:
            quality_checks.append("low_confidence")
        
        # Text length check
        if word_count >= 5:
            quality_checks.append("sufficient_text")
        elif word_count >= 2:
            quality_checks.append("minimal_text")
        else:
            quality_checks.append("insufficient_text")
        
        # Character pattern check (does it look like real text?)
        if _has_readable_patterns(extracted_text):
            quality_checks.append("readable_patterns")
        else:
            quality_checks.append("garbled_text")
        
        # Determine overall reliability
        is_reliable = (
            confidence >= min_confidence and 
            word_count >= 3 and 
            _has_readable_patterns(extracted_text)
        )
        
        # Generate recommendation
        if is_reliable:
            recommendation = "proceed"
        elif confidence < 30:
            recommendation = "image_quality_poor"
        elif word_count < 2:
            recommendation = "no_text_detected"
        else:
            recommendation = "manual_review"
        
        return {
            "is_reliable": is_reliable,
            "confidence": confidence,
            "quality_checks": quality_checks,
            "word_count": word_count,
            "recommendation": recommendation,
            "reason": f"Confidence: {confidence:.1f}%, Words: {word_count}, Pattern check: {'pass' if _has_readable_patterns(extracted_text) else 'fail'}"
        }
        
    except Exception as e:
        return {
            "is_reliable": False,
            "confidence": 0.0,
            "reason": f"Validation error: {str(e)}",
            "recommendation": "error"
        }

def _has_readable_patterns(text: str) -> bool:
    """Check if text has readable word patterns (not just random characters)"""
    if not text or len(text) < 3:
        return False
    
    # Check for common English patterns
    import re
    
    # Common event-related words
    event_words = [
        'event', 'show', 'concert', 'festival', 'workshop', 'class', 'meeting',
        'party', 'celebration', 'conference', 'seminar', 'exhibition', 'fair',
        'market', 'sale', 'performance', 'theater', 'dance', 'music', 'art',
        'food', 'drink', 'dinner', 'lunch', 'breakfast', 'brunch'
    ]
    
    # Common time/date words
    time_words = [
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
        'september', 'october', 'november', 'december', 'today', 'tomorrow',
        'tonight', 'morning', 'afternoon', 'evening', 'night', 'am', 'pm',
        'time', 'date', 'when', 'where', 'what', 'who'
    ]
    
    # Common location words
    location_words = [
        'at', 'in', 'on', 'near', 'downtown', 'center', 'hall', 'room', 'building',
        'street', 'avenue', 'road', 'drive', 'venue', 'location', 'address',
        'park', 'plaza', 'square', 'theater', 'auditorium', 'stadium', 'arena'
    ]
    
    text_lower = text.lower()
    all_keywords = event_words + time_words + location_words
    
    # Check for presence of known keywords
    keyword_matches = sum(1 for word in all_keywords if word in text_lower)
    
    # Check for basic English patterns
    has_vowels = bool(re.search(r'[aeiou]', text_lower))
    has_consonants = bool(re.search(r'[bcdfghjklmnpqrstvwxyz]', text_lower))
    has_spaces = ' ' in text
    has_numbers = bool(re.search(r'\d', text))
    
    # Text is readable if it has:
    # - At least one keyword match OR
    # - Basic English patterns (vowels, consonants, spaces)
    return (
        keyword_matches > 0 or
        (has_vowels and has_consonants and has_spaces) or
        (has_numbers and has_spaces)  # Dates, times, addresses
    )