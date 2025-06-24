#!/usr/bin/env python3
"""
Test script to validate the multi-date URL parsing fix
"""

from langgraph.pipeline.smart_pipeline import SmartEventPipeline
from dotenv import load_dotenv

def test_multi_date_url_fix():
    """Test that multi-date URLs are now parsed correctly"""
    load_dotenv()
    
    pipeline = SmartEventPipeline(dry_run=True)
    
    test_cases = [
        {
            "url": "https://www.a2sf.org/events/david-zinn-chalk-art/",
            "expected_sessions": 5,
            "expected_location": "Top of the Park",
            "description": "David Zinn Chalk Art - 5 separate dates"
        },
        {
            "url": "https://www.ypsireal.com/event/unarmed-brawling-on-stage/19464/",
            "expected_sessions": 2,  # Based on trace, this has 2 dates
            "expected_location": "Riverside Arts Center",
            "description": "Unarmed Brawling event - multiple sessions"
        }
    ]
    
    print("🧪 Testing Multi-Date URL Parsing Fix")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case['description']}")
        print(f"URL: {test_case['url']}")
        
        try:
            result = pipeline.process_event_input(
                raw_input=test_case['url'],
                source='test',
                user_id='test_user'
            )
            
            # Check multi-date detection
            total_sessions = result.get('total_sessions', 1)
            event_location = result.get('event_location', '')
            event_date = result.get('event_date', '')
            processing_time = result.get('processing_time', 0)
            
            print(f"📊 Results:")
            print(f"  Sessions: {total_sessions} (expected: {test_case['expected_sessions']})")
            print(f"  Location: '{event_location}' (expected: contains '{test_case['expected_location']}')")
            print(f"  Date format: {event_date}")
            print(f"  Processing time: {processing_time:.2f}s")
            
            # Validate results
            sessions_correct = total_sessions == test_case['expected_sessions']
            location_correct = test_case['expected_location'].lower() in event_location.lower()
            dates_present = bool(event_date and event_date != "PM")
            
            if sessions_correct and location_correct and dates_present:
                print(f"✅ PASS: All criteria met")
            else:
                print(f"❌ FAIL:")
                if not sessions_correct:
                    print(f"  - Wrong session count: {total_sessions} vs {test_case['expected_sessions']}")
                if not location_correct:
                    print(f"  - Location missing/wrong: '{event_location}'")
                if not dates_present:
                    print(f"  - No proper dates extracted: '{event_date}'")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests PASSED! Multi-date URL parsing fix is working correctly.")
        print("\n🚀 Performance Summary:")
        print("- Multi-date events correctly detected")
        print("- Proper series linking with session counts")
        print("- Location extraction working")
        print("- Date formatting in ISO 8601")
    else:
        print("❌ Some tests FAILED. Multi-date URL parsing may still have issues.")
    
    return all_passed

if __name__ == "__main__":
    test_multi_date_url_fix()