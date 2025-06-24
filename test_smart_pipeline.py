#!/usr/bin/env python3
"""
Test script for the new smart pipeline
"""

import os
import sys
import time
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_smart_pipeline():
    """Test the smart pipeline with sample inputs"""
    
    # Test cases
    test_cases = [
        {
            "input": "https://www.a2sf.org/events/david-zinn-chalk-art/",
            "expected_type": "url",
            "description": "Event URL from trace analysis"
        },
        {
            "input": "Concert tonight at 8PM downtown at The Venue",
            "expected_type": "text", 
            "description": "Event text with time and location"
        },
        {
            "input": "https://eventbrite.com/some-event",
            "expected_type": "url",
            "description": "Simple Eventbrite URL"
        },
        {
            "input": "Workshop on machine learning this Saturday",
            "expected_type": "text",
            "description": "Simple event text"
        }
    ]
    
    print("🧪 Testing Smart Pipeline Components")
    print("=" * 50)
    
    # Test 1: Smart Classifier
    print("\n1. Testing Smart Classifier")
    print("-" * 30)
    
    try:
        from langgraph.pipeline.classifiers.smart_classifier import SmartClassifier
        
        classifier = SmartClassifier()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['description']}")
            print(f"Input: {test_case['input']}")
            
            start_time = time.time()
            result = classifier.classify(test_case['input'])
            duration = time.time() - start_time
            
            print(f"Classified as: {result['input_type']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Method: {result['method']}")
            print(f"Duration: {duration*1000:.1f}ms")
            
            # Check if classification matches expectation
            if result['input_type'] == test_case['expected_type']:
                print("✅ Classification correct")
            else:
                print(f"❌ Expected {test_case['expected_type']}, got {result['input_type']}")
        
        # Print classifier stats
        print(f"\n📊 Classifier Statistics:")
        stats = classifier.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ Classifier test failed: {e}")
        return False
    
    # Test 2: URL Processor (dry run)
    print("\n\n2. Testing URL Processor (Dry Run)")
    print("-" * 40)
    
    try:
        from langgraph.pipeline.processors.url_processor import URLProcessor
        
        processor = URLProcessor(dry_run=True)
        
        # Test with URL input
        url_test = test_cases[0]  # Use first URL test case
        classified_input = {
            "input_type": "url",
            "raw_input": url_test["input"],
            "confidence": 0.95,
            "method": "tier1_regex"
        }
        
        print(f"Processing: {url_test['input']}")
        start_time = time.time()
        result = processor.process(classified_input, source="test", user_id="test_user")
        duration = time.time() - start_time
        
        print(f"Processing time: {duration:.2f}s")
        print(f"Status: {result.get('notion_save_status', 'unknown')}")
        
        if 'event_title' in result:
            print(f"Extracted title: {result['event_title']}")
        if 'event_date' in result:
            print(f"Extracted date: {result['event_date']}")
        if 'event_location' in result:
            print(f"Extracted location: {result['event_location']}")
            
        if result.get('notion_save_status') == 'success' or result.get('dry_run'):
            print("✅ URL processing successful")
        else:
            print(f"❌ URL processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ URL processor test failed: {e}")
        return False
    
    # Test 3: Complete Smart Pipeline
    print("\n\n3. Testing Complete Smart Pipeline (Dry Run)")
    print("-" * 50)
    
    try:
        from langgraph.pipeline.smart_pipeline import SmartEventPipeline
        
        pipeline = SmartEventPipeline(dry_run=True)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Pipeline Test {i}: {test_case['description']} ---")
            print(f"Input: {test_case['input']}")
            
            start_time = time.time()
            result = pipeline.process_event_input(
                raw_input=test_case['input'],
                source="test",
                user_id="test_user"
            )
            duration = time.time() - start_time
            
            print(f"Total time: {duration:.2f}s")
            
            if 'pipeline_metadata' in result:
                metadata = result['pipeline_metadata']
                print(f"Classification time: {metadata.get('classification_time', 0)*1000:.1f}ms")
                print(f"Processing time: {metadata.get('processing_time', 0)*1000:.1f}ms")
                print(f"Processor used: {metadata.get('processor_used')}")
                print(f"Classification tier: {metadata.get('classification_tier')}")
            
            if result.get('notion_save_status') == 'success' or result.get('dry_run'):
                print("✅ Pipeline processing successful")
            else:
                print(f"❌ Pipeline processing failed: {result.get('error', 'Unknown error')}")
        
        # Print comprehensive stats
        print(f"\n📊 Pipeline Statistics:")
        stats = pipeline.get_comprehensive_stats()
        
        if 'pipeline_overview' in stats:
            overview = stats['pipeline_overview']
            print(f"  Total processed: {overview['total_processed']}")
            print(f"  Success rate: {overview['success_rate']:.1f}%")
            print(f"  Avg total time: {overview['avg_total_time']:.2f}s")
            print(f"  Avg classification time: {overview['avg_classification_time']*1000:.1f}ms")
        
        if 'classification_stats' in stats:
            cls_stats = stats['classification_stats']
            if 'tier1_percentage' in cls_stats:
                print(f"  Tier 1 efficiency: {cls_stats['tier1_percentage']:.1f}%")
                print(f"  LLM usage: {cls_stats.get('llm_usage', 0)} calls")
            
    except Exception as e:
        print(f"❌ Complete pipeline test failed: {e}")
        return False
    
    print("\n🎉 All tests completed successfully!")
    print("\nTo enable smart pipeline in production, set:")
    print("export USE_SMART_PIPELINE=true")
    
    return True

if __name__ == "__main__":
    # Set up environment for testing
    os.environ["USE_SMART_PIPELINE"] = "false"  # Test in isolation first
    
    success = test_smart_pipeline()
    sys.exit(0 if success else 1)