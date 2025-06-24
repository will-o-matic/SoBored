#!/usr/bin/env python3
"""
Test script to validate the text processor prompt improvements for multi-date extraction
"""

from langgraph.pipeline.smart_pipeline import SmartEventPipeline
from dotenv import load_dotenv

def test_text_processor_prompt_improvements():
    """Test that the enhanced text processor prompt correctly handles multi-date events"""
    load_dotenv()
    
    pipeline = SmartEventPipeline(dry_run=True)
    
    test_cases = [
        {
            "name": "Original Failing Case - Workshop Series",
            "input": "Workshop series: Machine Learning Basics on June 24, June 26, and June 28 at 2PM each day at Tech Center Room 101",
            "expected_sessions": 3,
            "expected_dates": ["2025-06-24 14:00", "2025-06-26 14:00", "2025-06-28 14:00"],
            "description": "LangSmith trace b51775d9-9966-485d-9940-856c92f9c441 failing case"
        },
        {
            "name": "Simple Two-Date Event",
            "input": "Concert on June 15 and June 17 at 8PM",
            "expected_sessions": 2,
            "expected_dates": ["2025-06-15 20:00", "2025-06-17 20:00"],
            "description": "Simple explicit multi-date event"
        },
        {
            "name": "Seven Consecutive Dates",
            "input": "Daily meditation sessions: June 24, 25, 26, 27, 28, 29, 30 at 8AM",
            "expected_sessions": 7,
            "expected_dates": ["2025-06-24 08:00", "2025-06-25 08:00", "2025-06-26 08:00", "2025-06-27 08:00", "2025-06-28 08:00", "2025-06-29 08:00", "2025-06-30 08:00"],
            "description": "Explicit consecutive multi-date list"
        },
        {
            "name": "Recurring Pattern (Single Date)",
            "input": "Yoga class every Tuesday at 7PM starting June 24th for 8 weeks",
            "expected_sessions": 1,
            "expected_dates": ["2025-06-24 19:00"],
            "description": "Recurring pattern should extract only start date"
        },
        {
            "name": "Single Date Control",
            "input": "Meeting on June 25th at 2PM",
            "expected_sessions": 1,
            "expected_dates": ["2025-06-25 14:00"],
            "description": "Single date control case"
        }
    ]
    
    print("🧪 Testing Text Processor Prompt Improvements")
    print("=" * 70)
    print("Validating enhanced multi-date extraction capabilities")
    print("=" * 70)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Input: {test_case['input']}")
        print("-" * 50)
        
        try:
            result = pipeline.process_event_input(
                raw_input=test_case['input'],
                source='telegram',
                user_id=f'test_user_{i}'
            )
            
            # Extract results
            actual_sessions = result.get('total_sessions', 1)
            event_date = result.get('event_date', '')
            event_title = result.get('event_title', '')
            event_location = result.get('event_location', '')
            processing_time = result.get('processing_time', 0)
            
            # Parse actual dates
            if ',' in str(event_date):
                actual_dates = [d.strip() for d in str(event_date).split(',')]
            else:
                actual_dates = [event_date] if event_date else []
            
            print(f"📊 Results:")
            print(f"  Title: {event_title}")
            print(f"  Location: {event_location}")
            print(f"  Sessions: {actual_sessions} (expected: {test_case['expected_sessions']})")
            print(f"  Processing time: {processing_time:.2f}s")
            print(f"  Dates extracted: {len(actual_dates)}")
            
            # Validate results
            sessions_correct = actual_sessions == test_case['expected_sessions']
            dates_count_correct = len(actual_dates) == len(test_case['expected_dates'])
            
            # Check date accuracy
            dates_accurate = True
            if dates_count_correct:
                for j, expected_date in enumerate(test_case['expected_dates']):
                    if j < len(actual_dates):
                        if actual_dates[j] != expected_date:
                            dates_accurate = False
                            break
            
            if sessions_correct and dates_count_correct and dates_accurate:
                print(f"✅ PASS: All criteria met")
                print(f"  Expected dates: {test_case['expected_dates']}")
                print(f"  Actual dates: {actual_dates}")
            else:
                print(f"❌ FAIL:")
                if not sessions_correct:
                    print(f"  - Wrong session count: {actual_sessions} vs {test_case['expected_sessions']}")
                if not dates_count_correct:
                    print(f"  - Wrong date count: {len(actual_dates)} vs {len(test_case['expected_dates'])}")
                if not dates_accurate:
                    print(f"  - Date accuracy issue:")
                    print(f"    Expected: {test_case['expected_dates']}")
                    print(f"    Actual: {actual_dates}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All text processor prompt tests PASSED!")
        print("\n🚀 Improvements Successfully Implemented:")
        print("- ✅ Multi-date extraction from explicit date lists")
        print("- ✅ Proper distinction between explicit dates vs recurring patterns")
        print("- ✅ Comma-separated date output for multi-instance events")
        print("- ✅ Maintains single-date event handling")
        print("- ✅ Proper date formatting with current year context")
        print("\n📈 Performance Impact:")
        print("- Original failing case now works perfectly")
        print("- Multi-date text events now create proper series with session counts")
        print("- Evaluation framework will show improved scoring")
    else:
        print("❌ Some text processor tests FAILED. Further prompt refinement needed.")
    
    return all_passed

if __name__ == "__main__":
    test_text_processor_prompt_improvements()