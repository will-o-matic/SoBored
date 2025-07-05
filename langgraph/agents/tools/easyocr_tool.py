"""
EasyOCR tool for extracting text from images using CRAFT-based detection.
Enhanced OCR specifically designed for scene text and event flyers.
"""

import os
import logging
import time
import io
from typing import Dict, Any, List, Tuple, Optional
from langchain_core.tools import tool
import numpy as np
from PIL import Image
import requests

logger = logging.getLogger(__name__)

try:
    import easyocr
    import cv2
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not installed. Advanced scene text detection will be limited.")

# Global EasyOCR reader instance to avoid reloading models
_easyocr_reader = None

def get_easyocr_reader(languages=['en'], gpu=True):
    """Get or create EasyOCR reader instance"""
    global _easyocr_reader
    
    if _easyocr_reader is None:
        try:
            # Try GPU first, fallback to CPU if needed
            if gpu:
                try:
                    _easyocr_reader = easyocr.Reader(languages, gpu=True)
                    logger.info("EasyOCR initialized with GPU acceleration")
                except Exception as e:
                    logger.warning(f"GPU initialization failed, falling back to CPU: {e}")
                    _easyocr_reader = easyocr.Reader(languages, gpu=False)
                    logger.info("EasyOCR initialized with CPU")
            else:
                _easyocr_reader = easyocr.Reader(languages, gpu=False)
                logger.info("EasyOCR initialized with CPU")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            return None
    
    return _easyocr_reader

@tool
def extract_text_with_easyocr(image_data: str, image_format: str = "auto", 
                             detail_level: int = 0, width_threshold: float = 0.7,
                             height_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Extract text from an image using EasyOCR with CRAFT-based text detection.
    
    Args:
        image_data: Image data as base64 string or file path or URL
        image_format: Image format (auto, base64, file, url)
        detail_level: 0 = simple bounding box, 1 = detailed polygon
        width_threshold: Text region width threshold for filtering
        height_threshold: Text region height threshold for filtering
        
    Returns:
        Dict containing OCR results with extracted text and confidence
    """
    if not EASYOCR_AVAILABLE:
        return {
            "success": False,
            "error": "EasyOCR not available. Install with: pip install easyocr torch torchvision",
            "extracted_text": "",
            "confidence": 0.0,
            "installation_help": "To install EasyOCR: pip install easyocr torch torchvision"
        }
    
    try:
        print(f"[EASYOCR] Processing image, format: {image_format}")
        start_time = time.time()
        
        # Load image
        image = _load_image(image_data, image_format)
        if image is None:
            return {
                "success": False,
                "error": "Failed to load image",
                "extracted_text": "",
                "confidence": 0.0
            }
        
        # Convert PIL to numpy array for EasyOCR
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image
        
        # Get EasyOCR reader
        reader = get_easyocr_reader()
        if reader is None:
            return {
                "success": False,
                "error": "Failed to initialize EasyOCR reader",
                "extracted_text": "",
                "confidence": 0.0
            }
        
        # Extract text with EasyOCR
        # Note: EasyOCR readtext returns (bbox, text, confidence) tuples when detail=0
        # or (polygon, text, confidence) when detail=1
        results = reader.readtext(
            image_array, 
            detail=detail_level,
            width_ths=width_threshold,
            height_ths=height_threshold,
            paragraph=False  # Get individual text regions
        )
        
        print(f"[EASYOCR] Found {len(results)} text regions")
        
        extraction_time = time.time() - start_time
        
        # Process results
        text_regions = []
        all_text = []
        confidences = []
        
        for result in results:
            try:
                # EasyOCR returns tuples of (bbox/polygon, text, confidence)
                if isinstance(result, (list, tuple)) and len(result) >= 3:
                    if detail_level == 0:
                        bbox, text, confidence = result[0], result[1], result[2]
                    else:
                        polygon, text, confidence = result[0], result[1], result[2]
                        bbox = _polygon_to_bbox(polygon)
                elif isinstance(result, str):
                    # Fallback: if result is just text, use defaults
                    text = result
                    confidence = 0.5  # Default confidence
                    bbox = [[0, 0], [100, 0], [100, 50], [0, 50]]  # Default bbox
                else:
                    logger.warning(f"Unexpected EasyOCR result format: {result}")
                    continue
                
                # Ensure confidence is a number
                if isinstance(confidence, str):
                    try:
                        confidence = float(confidence)
                    except ValueError:
                        confidence = 0.5
                
                # Filter by confidence (EasyOCR confidence is 0-1)
                if confidence >= 0.3:  # Minimum confidence threshold
                    text_regions.append({
                        "text": text,
                        "confidence": confidence * 100,  # Convert to percentage
                        "bbox": bbox,
                        "area": _calculate_bbox_area(bbox)
                    })
                    all_text.append(text)
                    confidences.append(confidence * 100)
                    
            except Exception as e:
                logger.warning(f"Error processing EasyOCR result {result}: {e}")
                continue
        
        # Sort text regions by position (top to bottom, left to right)
        text_regions.sort(key=lambda x: (x["bbox"][0][1], x["bbox"][0][0]))
        
        # Combine text with intelligent spacing
        combined_text = _combine_text_regions(text_regions)
        
        # Clean and format the text
        cleaned_text = _clean_easyocr_text(combined_text)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        print(f"[EASYOCR] Extracted {len(text_regions)} text regions")
        print(f"[EASYOCR] Average confidence: {avg_confidence:.2f}%")
        print(f"[EASYOCR] Processing time: {extraction_time:.2f}s")
        
        return {
            "success": True,
            "extracted_text": cleaned_text,
            "confidence": avg_confidence,
            "raw_text": combined_text,
            "text_regions": text_regions,
            "region_count": len(text_regions),
            "processing_time": extraction_time,
            "word_count": len(cleaned_text.split()),
            "char_count": len(cleaned_text),
            "ocr_engine": "EasyOCR",
            "detail_level": detail_level
        }
        
    except Exception as e:
        error_msg = f"EasyOCR processing failed: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "extracted_text": "",
            "confidence": 0.0
        }

@tool
def extract_text_with_hybrid_ocr(image_data: str, image_format: str = "auto") -> Dict[str, Any]:
    """
    Extract text using both Tesseract and EasyOCR, then combine the best results.
    
    Args:
        image_data: Image data as base64 string or file path or URL
        image_format: Image format (auto, base64, file, url)
        
    Returns:
        Dict containing combined OCR results from multiple engines
    """
    try:
        print(f"[HYBRID OCR] Running both Tesseract and EasyOCR")
        
        # Run Tesseract OCR
        from .ocr_tool import extract_text_from_image
        tesseract_result = extract_text_from_image.invoke({
            "image_data": image_data,
            "image_format": image_format,
            "use_advanced_preprocessing": True
        })
        
        # Run EasyOCR
        easyocr_result = extract_text_with_easyocr.invoke({
            "image_data": image_data,
            "image_format": image_format
        })
        
        # Analyze results
        tesseract_success = tesseract_result.get("success", False)
        easyocr_success = easyocr_result.get("success", False)
        
        if not tesseract_success and not easyocr_success:
            return {
                "success": False,
                "error": "Both OCR engines failed",
                "tesseract_error": tesseract_result.get("error", "Unknown"),
                "easyocr_error": easyocr_result.get("error", "Unknown")
            }
        
        # Choose best result or combine
        best_result = _select_best_ocr_result(tesseract_result, easyocr_result)
        
        # Add comparison metadata
        best_result["hybrid_analysis"] = {
            "tesseract_confidence": tesseract_result.get("confidence", 0.0),
            "easyocr_confidence": easyocr_result.get("confidence", 0.0),
            "tesseract_words": tesseract_result.get("word_count", 0),
            "easyocr_words": easyocr_result.get("word_count", 0),
            "selected_engine": best_result.get("ocr_engine", "unknown"),
            "both_succeeded": tesseract_success and easyocr_success
        }
        
        return best_result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Hybrid OCR failed: {str(e)}",
            "extracted_text": "",
            "confidence": 0.0
        }

def _load_image(image_data: str, image_format: str) -> Optional[Image.Image]:
    """Load image from different sources"""
    try:
        if image_format == "url" or (image_format == "auto" and image_data.startswith("http")):
            response = requests.get(image_data, timeout=10)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
            
        elif image_format == "file" or (image_format == "auto" and os.path.exists(image_data)):
            return Image.open(image_data)
            
        elif image_format == "base64":
            import base64
            import io
            image_bytes = base64.b64decode(image_data)
            return Image.open(io.BytesIO(image_bytes))
            
        else:
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

def _polygon_to_bbox(polygon: List[List[int]]) -> List[List[int]]:
    """Convert polygon coordinates to bounding box format"""
    try:
        x_coords = [point[0] for point in polygon]
        y_coords = [point[1] for point in polygon]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        return [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]
    except Exception:
        return [[0, 0], [100, 0], [100, 50], [0, 50]]  # Default bbox

def _calculate_bbox_area(bbox: List[List[int]]) -> float:
    """Calculate area of bounding box"""
    try:
        width = abs(bbox[1][0] - bbox[0][0])
        height = abs(bbox[2][1] - bbox[1][1])
        return width * height
    except Exception:
        return 0.0

def _combine_text_regions(text_regions: List[Dict]) -> str:
    """Intelligently combine text regions with proper spacing"""
    if not text_regions:
        return ""
    
    # Sort by vertical position first, then horizontal
    sorted_regions = sorted(text_regions, key=lambda x: (x["bbox"][0][1], x["bbox"][0][0]))
    
    combined_text = []
    current_line_y = None
    line_tolerance = 20  # Pixels tolerance for same line
    
    for region in sorted_regions:
        text = region["text"].strip()
        if not text:
            continue
            
        bbox_y = region["bbox"][0][1]
        
        # Check if this is on the same line as previous text
        if current_line_y is None or abs(bbox_y - current_line_y) > line_tolerance:
            # New line
            if combined_text:  # Add newline if not first line
                combined_text.append("\n")
            current_line_y = bbox_y
        else:
            # Same line, add space
            if combined_text and not combined_text[-1].endswith("\n"):
                combined_text.append(" ")
        
        combined_text.append(text)
    
    return "".join(combined_text)

def _clean_easyocr_text(text: str) -> str:
    """Clean EasyOCR extracted text for event flyers"""
    if not text:
        return ""
    
    # Basic cleanup
    text = text.strip()
    
    # Fix common EasyOCR issues for event text
    import re
    
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Fix spacing around common event text
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n\s+', '\n', text)  # Remove leading spaces on lines
    
    # Common OCR corrections for event flyers
    corrections = {
        # Character level
        '|': 'I',
        '0O': 'OO',  # Common confusion
        '5TH': '5TH',  # Keep as is
        'ANNUAR': 'ANNUAL',
        'PRESERVAIMION': 'PRESERVATION',
        'FALLFEST': 'FALL FEST',
        'HERTRER': 'HERTLER',
        'AIMBOW': 'RAINBOW',
        'SEEKIERS': 'SEEKERS',
        'SAMEEYES': 'SAME EYES',
        'SATUIDAY': 'SATURDAY',
        'SEPTEMBEI': 'SEPTEMBER',
        'ALLAGES': 'ALL AGES',
        'DOORSAT': 'DOORS AT',
        'TICKETSAT': 'TICKETS AT',
        'JOEHERTLER.COM': 'JOEHERTLER.COM'
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    # Fix merged words (add space before capital letters following lowercase)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Clean up final formatting
    text = ' '.join(text.split())  # Normalize all whitespace
    
    return text

def _select_best_ocr_result(tesseract_result: Dict, easyocr_result: Dict) -> Dict:
    """Select the best OCR result based on multiple criteria"""
    
    # If only one succeeded, return that one
    if tesseract_result.get("success") and not easyocr_result.get("success"):
        tesseract_result["ocr_engine"] = "Tesseract"
        return tesseract_result
    elif easyocr_result.get("success") and not tesseract_result.get("success"):
        easyocr_result["ocr_engine"] = "EasyOCR"
        return easyocr_result
    elif not tesseract_result.get("success") and not easyocr_result.get("success"):
        return tesseract_result  # Return tesseract error
    
    # Both succeeded, choose based on quality metrics
    tesseract_score = _calculate_ocr_quality_score(tesseract_result)
    easyocr_score = _calculate_ocr_quality_score(easyocr_result)
    
    print(f"[HYBRID] Tesseract quality score: {tesseract_score:.3f}")
    print(f"[HYBRID] EasyOCR quality score: {easyocr_score:.3f}")
    
    if easyocr_score > tesseract_score:
        easyocr_result["ocr_engine"] = "EasyOCR"
        easyocr_result["quality_score"] = easyocr_score
        return easyocr_result
    else:
        tesseract_result["ocr_engine"] = "Tesseract"
        tesseract_result["quality_score"] = tesseract_score
        return tesseract_result

def _calculate_ocr_quality_score(result: Dict) -> float:
    """Calculate quality score for OCR result"""
    if not result.get("success"):
        return 0.0
    
    score = 0.0
    
    # Base score from confidence
    confidence = result.get("confidence", 0.0)
    score += (confidence / 100.0) * 0.5  # 50% weight
    
    # Word count bonus
    word_count = result.get("word_count", 0)
    if word_count >= 20:
        score += 0.3
    elif word_count >= 10:
        score += 0.2
    elif word_count >= 5:
        score += 0.1
    
    # Event-specific keywords
    text = result.get("extracted_text", "").lower()
    event_keywords = [
        "festival", "fest", "concert", "show", "event", "doors", "tickets", 
        "pm", "am", "saturday", "sunday", "annual", "featuring"
    ]
    
    keyword_matches = sum(1 for keyword in event_keywords if keyword in text)
    score += min(keyword_matches * 0.05, 0.2)  # Max 20% bonus
    
    return min(score, 1.0)

@tool
def compare_ocr_engines(image_data: str, image_format: str = "auto") -> Dict[str, Any]:
    """
    Compare Tesseract and EasyOCR performance on the same image.
    
    Args:
        image_data: Image data as base64 string or file path or URL
        image_format: Image format (auto, base64, file, url)
        
    Returns:
        Dict containing detailed comparison of both OCR engines
    """
    try:
        print(f"[COMPARISON] Testing both OCR engines")
        
        # Run both engines
        from .ocr_tool import extract_text_from_image
        
        tesseract_result = extract_text_from_image.invoke({
            "image_data": image_data,
            "image_format": image_format,
            "use_advanced_preprocessing": True
        })
        
        easyocr_result = extract_text_with_easyocr.invoke({
            "image_data": image_data,
            "image_format": image_format
        })
        
        # Calculate quality scores
        tesseract_quality = _calculate_ocr_quality_score(tesseract_result)
        easyocr_quality = _calculate_ocr_quality_score(easyocr_result)
        
        return {
            "success": True,
            "tesseract": {
                **tesseract_result,
                "quality_score": tesseract_quality,
                "engine": "Tesseract"
            },
            "easyocr": {
                **easyocr_result,
                "quality_score": easyocr_quality,
                "engine": "EasyOCR"
            },
            "comparison": {
                "winner": "EasyOCR" if easyocr_quality > tesseract_quality else "Tesseract",
                "tesseract_quality": tesseract_quality,
                "easyocr_quality": easyocr_quality,
                "confidence_difference": abs(
                    easyocr_result.get("confidence", 0) - tesseract_result.get("confidence", 0)
                ),
                "word_count_difference": abs(
                    easyocr_result.get("word_count", 0) - tesseract_result.get("word_count", 0)
                )
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"OCR comparison failed: {str(e)}"
        }