#!/usr/bin/env python3
"""
Test script to debug image parsing issues
"""
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_image_parsing():
    """Test the image parsing logic with actual EasyOCR text"""
    load_dotenv()
    
    # This is the exact text EasyOCR extracted
    easyocr_text = "sth ANNUAL PRESERVATION FALL FEST FEATURING JOE HERTLER & THE RAINBOW SEEKERS ntt PAJAMAS AND SAME EYES LIVE AT HOMES CAMPUS ANN ARBOR; MI SATURDAY, SEPTEMBER 13 ALL AGES Doo RS AT 6PM TICKETS AT JOEHERTLER COM"
    
    print("🔍 Testing image parsing with EasyOCR text:")
    print(f"Input text: {easyocr_text}")
    print("=" * 80)
    
    try:
        from langgraph.pipeline.processors.image_processor import ImageProcessor
        
        processor = ImageProcessor()
        
        # Test the LLM parsing directly
        result = processor._llm_parse_ocr_text(easyocr_text)
        
        print("📋 Parsed Event Details:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Title: {result.get('event_title', 'N/A')}")
        print(f"  Date: {result.get('event_date', 'N/A')}")
        print(f"  Location: {result.get('event_location', 'N/A')}")
        print(f"  Description: {result.get('event_description', 'N/A')}")
        print(f"  Confidence: {result.get('parsing_confidence', 'N/A')}")
        
        if 'ocr_corrections' in result:
            print(f"  OCR Corrections: {result['ocr_corrections']}")
        
        if 'error' in result:
            print(f"  Error: {result['error']}")
            
        # Check for comma in date field
        event_date = result.get('event_date', '')
        if ',' in str(event_date):
            print(f"\n⚠️  WARNING: Date field contains comma: '{event_date}'")
            print("This will trigger multi-session creation!")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing image parsing: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_image_parsing()