#!/usr/bin/env python3
"""
Test script for image processing pipeline

Usage:
    python test_image_processing.py [image_path] [--dry-run] [--verbose]

Examples:
    python test_image_processing.py ./test_image.jpg --dry-run
    python test_image_processing.py ./event_flyer.png --verbose
    python test_image_processing.py --interactive --dry-run
"""

import os
import sys
import argparse
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_ocr_tool(image_path: str, verbose: bool = False):
    """Test OCR tool functionality"""
    try:
        from langgraph.agents.tools.ocr_tool import extract_text_from_image, validate_ocr_quality
        
        print(f"🔍 Testing OCR extraction on: {image_path}")
        
        # Extract text
        ocr_result = extract_text_from_image.invoke({
            "image_data": image_path,
            "image_format": "auto"
        })
        
        if verbose:
            print(f"📄 Raw OCR Result:")
            print(json.dumps(ocr_result, indent=2))
        
        # Validate quality
        validation_result = validate_ocr_quality.invoke({
            "ocr_result": ocr_result,
            "min_confidence": 70.0
        })
        
        print(f"✅ OCR Success: {ocr_result.get('success', False)}")
        print(f"📊 Confidence: {ocr_result.get('confidence', 0.0):.1f}%")
        print(f"📝 Extracted Text ({ocr_result.get('word_count', 0)} words):")
        print(f"   {ocr_result.get('extracted_text', '')[:200]}{'...' if len(ocr_result.get('extracted_text', '')) > 200 else ''}")
        print(f"🎯 Quality Assessment: {'✅ Reliable' if validation_result.get('is_reliable', False) else '⚠️ Unreliable'}")
        print(f"💡 Recommendation: {validation_result.get('recommendation', 'unknown')}")
        
        return ocr_result, validation_result
        
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return None, None

def test_image_processor(image_path: str, dry_run: bool = True, verbose: bool = False):
    """Test full image processing pipeline"""
    try:
        from langgraph.pipeline.processors.image_processor import ImageProcessor
        
        print(f"\n🚀 Testing Image Processor Pipeline")
        
        # Create processor
        processor = ImageProcessor(dry_run=dry_run)
        
        # Create classified input (simulating smart classifier output)
        classified_input = {
            "input_type": "image",
            "raw_input": f"[image uploaded: {os.path.basename(image_path)}]",
            "confidence": 0.95,
            "method": "tier1_regex",
            "reasoning": "Image file detected",
            "image_data": image_path  # Direct file path for testing
        }
        
        # Process image
        result = processor.process(
            classified_input=classified_input,
            source="test_script",
            user_id="test_user"
        )
        
        if verbose:
            print(f"📋 Full Processing Result:")
            print(json.dumps(result, indent=2, default=str))
        
        # Extract key information
        success = result.get("notion_save_status") == "success" or result.get("pending_confirmation")
        processing_time = result.get("processing_time", 0.0)
        
        print(f"✅ Processing Success: {success}")
        print(f"⏱️ Processing Time: {processing_time:.2f}s")
        
        # Event extraction results
        if "event_title" in result:
            print(f"📌 Event Title: {result.get('event_title', 'N/A')}")
            print(f"📅 Event Date: {result.get('event_date', 'N/A')}")
            print(f"📍 Event Location: {result.get('event_location', 'N/A')}")
            print(f"📝 Description: {result.get('event_description', 'N/A')[:100]}{'...' if len(result.get('event_description', '')) > 100 else ''}")
        
        # Confirmation handling
        if result.get("confirmation_required", False):
            print(f"\n📋 CONFIRMATION REQUIRED:")
            print(f"Reasons: {', '.join(result.get('confirmation_reasons', []))}")
            print(f"\nUser Message:")
            print(result.get("confirmation_message", "No message generated"))
        
        # Statistics
        print(f"\n📊 Processor Statistics:")
        stats = processor.get_stats()
        if isinstance(stats, dict) and "processing_stats" in stats:
            print(f"   Processing: {stats['processing_stats']}")
            print(f"   OCR: {stats['ocr_stats']}")
        else:
            print(f"   {stats}")
        
        return result
        
    except Exception as e:
        print(f"❌ Image processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_smart_pipeline_integration(image_path: str, dry_run: bool = True, verbose: bool = False):
    """Test full smart pipeline integration"""
    try:
        from langgraph.pipeline.smart_pipeline import process_with_smart_pipeline
        
        print(f"\n🔗 Testing Smart Pipeline Integration")
        
        # Simulate Telegram image data
        telegram_data = {
            "photo": [{"file_id": "test_file_id", "file_size": 1024}],
            "chat_id": 12345,
            "message_id": 67890,
            "caption": f"Test image: {os.path.basename(image_path)}"
        }
        
        # For testing, we'll modify the raw_input to include the file path
        # In real usage, Telegram would provide the file_id
        raw_input = f"[image uploaded: {image_path}]"  # Include path for testing
        
        # Process with smart pipeline
        result = process_with_smart_pipeline(
            raw_input=raw_input,
            source="test_script",
            user_id="test_user",
            dry_run=dry_run,
            telegram_data=telegram_data
        )
        
        if verbose:
            print(f"📋 Smart Pipeline Result:")
            print(json.dumps(result, indent=2, default=str))
        
        # Extract key metrics
        pipeline_metadata = result.get("pipeline_metadata", {})
        total_time = pipeline_metadata.get("total_pipeline_time", 0.0)
        classification_time = pipeline_metadata.get("classification_time", 0.0)
        processing_time = pipeline_metadata.get("processing_time", 0.0)
        processor_used = pipeline_metadata.get("processor_used", "unknown")
        
        print(f"✅ Pipeline Success: {not result.get('error')}")
        print(f"🔧 Processor Used: {processor_used}")
        print(f"⏱️ Total Time: {total_time:.2f}s")
        print(f"   Classification: {classification_time:.3f}s")
        print(f"   Processing: {processing_time:.2f}s")
        
        return result
        
    except Exception as e:
        print(f"❌ Smart pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def interactive_mode():
    """Interactive testing mode"""
    print("🎯 Interactive Image Processing Test Mode")
    print("Enter image paths to test (or 'quit' to exit)")
    
    while True:
        try:
            image_path = input("\n📁 Image path: ").strip()
            if image_path.lower() in ['quit', 'exit', 'q']:
                break
            
            if not os.path.exists(image_path):
                print(f"❌ File not found: {image_path}")
                continue
            
            dry_run = input("🧪 Dry run mode? (y/n) [y]: ").strip().lower()
            dry_run = dry_run != 'n'
            
            verbose = input("📝 Verbose output? (y/n) [n]: ").strip().lower()
            verbose = verbose == 'y'
            
            print(f"\n{'='*50}")
            
            # Run tests
            test_ocr_tool(image_path, verbose)
            test_image_processor(image_path, dry_run, verbose)
            test_smart_pipeline_integration(image_path, dry_run, verbose)
            
            print(f"{'='*50}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error in interactive mode: {e}")

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Test image processing pipeline")
    parser.add_argument("image_path", nargs="?", help="Path to test image")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run in dry-run mode (default)")
    parser.add_argument("--production", action="store_true", help="Run in production mode (saves to Notion)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--ocr-only", action="store_true", help="Test OCR only")
    parser.add_argument("--processor-only", action="store_true", help="Test processor only")
    parser.add_argument("--pipeline-only", action="store_true", help="Test pipeline only")
    
    args = parser.parse_args()
    
    # Set dry_run mode
    dry_run = not args.production
    
    if args.interactive:
        interactive_mode()
        return
    
    if not args.image_path:
        print("❌ No image path provided. Use --interactive for interactive mode.")
        parser.print_help()
        return
    
    if not os.path.exists(args.image_path):
        print(f"❌ Image file not found: {args.image_path}")
        return
    
    print(f"🧪 Testing Image Processing Pipeline")
    print(f"📁 Image: {args.image_path}")
    print(f"🔧 Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print(f"{'='*50}")
    
    # Run requested tests
    if args.ocr_only:
        test_ocr_tool(args.image_path, args.verbose)
    elif args.processor_only:
        test_image_processor(args.image_path, dry_run, args.verbose)
    elif args.pipeline_only:
        test_smart_pipeline_integration(args.image_path, dry_run, args.verbose)
    else:
        # Run all tests
        test_ocr_tool(args.image_path, args.verbose)
        test_image_processor(args.image_path, dry_run, args.verbose)
        test_smart_pipeline_integration(args.image_path, dry_run, args.verbose)

if __name__ == "__main__":
    main()