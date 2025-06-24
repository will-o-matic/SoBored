#!/usr/bin/env python3
"""
Test LangSmith tracing structure for smart pipeline
"""

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_smart_pipeline_tracing():
    """Test smart pipeline with LangSmith tracing enabled"""
    
    # Ensure LangSmith is configured
    os.environ["USE_SMART_PIPELINE"] = "true"
    
    # Test with the URL from the original trace
    test_url = "https://www.a2sf.org/events/david-zinn-chalk-art/"
    
    print("🔍 Testing Smart Pipeline LangSmith Tracing")
    print("=" * 50)
    print(f"Test URL: {test_url}")
    print(f"Smart Pipeline Enabled: {os.getenv('USE_SMART_PIPELINE')}")
    
    try:
        # Import and use the main agent function (which should route to smart pipeline)
        from langgraph.main_agent import process_event_input
        
        print("\n📊 Processing with Smart Pipeline...")
        start_time = time.time()
        
        result = process_event_input(
            raw_input=test_url,
            source="test_tracing",
            user_id="test_user_123",
            dry_run=True  # Use dry run to avoid actual Notion saves
        )
        
        duration = time.time() - start_time
        
        print(f"\n✅ Processing completed in {duration:.2f}s")
        print(f"Processing method: {result.get('processing_method', 'unknown')}")
        
        if 'pipeline_metadata' in result:
            metadata = result['pipeline_metadata']
            print(f"Pipeline type: {metadata.get('pipeline_type')}")
            print(f"Classification tier: {metadata.get('classification_tier')}")
            print(f"Processor used: {metadata.get('processor_used')}")
            print(f"Classification time: {metadata.get('classification_time', 0)*1000:.1f}ms")
            print(f"Processing time: {metadata.get('processing_time', 0)*1000:.1f}ms")
        
        if 'event_title' in result:
            print(f"\nExtracted Event Data:")
            print(f"  Title: {result.get('event_title', 'N/A')}")
            print(f"  Date: {result.get('event_date', 'N/A')}")
            print(f"  Location: {result.get('event_location', 'N/A')}")
        
        print(f"\n📋 What you should see in LangSmith:")
        print(f"1. 'Smart Event Processing Pipeline' (parent run)")
        print(f"2.   ├── 'Smart Input Classification' (child run)")  
        print(f"3.   ├── 'Url Event Processing' (child run)")
        print(f"4.   │   ├── fetch_url_content (tool run)")
        print(f"5.   │   ├── parse_url_content (tool run)")
        print(f"6.   │   └── save_to_notion (tool run)")
        print(f"7.   └── (final outputs)")
        
        if result.get('processing_method') == 'smart_pipeline':
            print(f"\n✅ Smart pipeline was used successfully!")
        else:
            print(f"\n⚠️  ReAct agent was used instead. Check USE_SMART_PIPELINE flag.")
            
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_smart_pipeline_tracing()
    
    if success:
        print(f"\n🎯 Next Steps:")
        print(f"1. Check LangSmith web UI for the trace hierarchy")
        print(f"2. Look for 'Smart Event Processing Pipeline' runs")
        print(f"3. Verify tool runs are nested properly")
        print(f"4. If tools are still top-level, we need to adjust context propagation")
    
    sys.exit(0 if success else 1)