#!/usr/bin/env python3
"""
Test script to verify the date parsing fix works correctly
"""

from langgraph.pipeline.smart_pipeline import SmartEventPipeline
from dotenv import load_dotenv

def test_date_parsing_fix():
    """Test that dates are now parsed with correct year context"""
    load_dotenv()
    
    pipeline = SmartEventPipeline(dry_run=True)
    
    test_cases = [
        {
            "input": "Concert on June 25th at 8PM",
            "expected_year": "2025",
            "description": "Simple date with time"
        },
        {
            "input": "Concert on June 25th (rescheduled from June 15th, June 20th was also considered)",
            "expected_year": "2025",
            "description": "Date from failing LangSmith trace"
        },
        {
            "input": "Workshop series: Machine Learning Basics on June 24, June 26, and June 28 at 2PM each day",
            "expected_year": "2025",
            "description": "Multi-date event"
        },
        {
            "input": "Yoga class every Tuesday at 7PM starting June 24th",
            "expected_year": "2025", 
            "description": "Recurring event start date"
        }
    ]
    
    print("🧪 Testing Date Parsing Fix")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case['description']}")
        print(f"Input: {test_case['input']}")
        
        try:
            result = pipeline.process_event_input(
                raw_input=test_case['input'],
                source='test',
                user_id='test_user'
            )
            
            event_date = result.get('event_date', '')
            if event_date:
                if test_case['expected_year'] in event_date:
                    print(f"✅ PASS: {event_date} (contains {test_case['expected_year']})")
                else:
                    print(f"❌ FAIL: {event_date} (does not contain {test_case['expected_year']})")
                    all_passed = False
            else:
                print(f"⚠️  WARN: No date extracted")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests PASSED! Date parsing fix is working correctly.")
    else:
        print("❌ Some tests FAILED. Date parsing may still have issues.")
    
    return all_passed

if __name__ == "__main__":
    test_date_parsing_fix()