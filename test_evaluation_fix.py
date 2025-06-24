#!/usr/bin/env python3
"""
Test script to validate the evaluation framework fixes for multi-date events
"""

from langgraph.evaluation.multi_date_evaluator import MultiDateEventEvaluator
from langsmith import Client

def test_evaluation_fixes():
    """Test that the evaluation framework now correctly handles multi-date events"""
    
    print("🧪 Testing Evaluation Framework Fixes")
    print("=" * 60)
    
    # Create evaluator (warning about missing API key is expected)
    client = Client()
    evaluator = MultiDateEventEvaluator(client)
    
    test_cases = [
        {
            "name": "David Zinn Multi-Date Event (5 sessions)",
            "inputs": {
                "source": "telegram",
                "user_id": "test_user_2",
                "raw_input": "https://www.a2sf.org/events/david-zinn-chalk-art/"
            },
            "outputs": {
                "event_date": "2025-06-15 17:00, 2025-06-18 17:00, 2025-06-22 17:00, 2025-06-24 17:00, 2025-06-29 17:00",
                "total_sessions": 5
            },
            "reference_outputs": {
                "expected_dates": ["2025-06-15 17:00", "2025-06-18 17:00", "2025-06-22 17:00", "2025-06-24 17:00", "2025-06-29 17:00"],
                "expected_behavior": "multi_instance",
                "expected_sessions": 5,
                "expected_series_linking": True
            }
        },
        {
            "name": "Single Date Event (control case)",
            "inputs": {
                "source": "telegram",
                "user_id": "test_user_3",
                "raw_input": "Concert on June 25th at 8PM"
            },
            "outputs": {
                "event_date": "2025-06-25 20:00",
                "total_sessions": 1
            },
            "reference_outputs": {
                "expected_dates": ["2025-06-25 20:00"],
                "expected_behavior": "single_instance",
                "expected_sessions": 1,
                "expected_series_linking": False
            }
        },
        {
            "name": "Broken Date Format (should fail)",
            "inputs": {
                "source": "telegram", 
                "user_id": "test_user_4",
                "raw_input": "Some event"
            },
            "outputs": {
                "event_date": "PM",  # This should fail validation
                "total_sessions": 1
            },
            "reference_outputs": {
                "expected_dates": ["2025-06-25 20:00"],
                "expected_behavior": "single_instance", 
                "expected_sessions": 1,
                "expected_series_linking": False
            }
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case['name']}")
        print("-" * 40)
        
        # Test multi-date detection
        detection_result = evaluator.multi_date_detection_evaluator(
            test_case["inputs"], 
            test_case["outputs"], 
            test_case["reference_outputs"]
        )
        
        # Test date formatting
        formatting_result = evaluator.date_formatting_evaluator(
            test_case["inputs"],
            test_case["outputs"], 
            test_case["reference_outputs"]
        )
        
        print(f"📊 Multi-Date Detection:")
        print(f"  Score: {detection_result.get('score')}")
        print(f"  Value: {detection_result.get('value')}")
        
        print(f"📅 Date Formatting:")
        print(f"  Score: {formatting_result.get('score')}")
        print(f"  Value: {formatting_result.get('value')}")
        print(f"  Dates checked: {formatting_result.get('details', {}).get('total_dates_checked')}")
        
        # Determine expected results
        should_detect_multi = test_case["reference_outputs"]["expected_behavior"] == "multi_instance"
        should_format_correctly = test_case["outputs"]["event_date"] != "PM"
        
        detection_passed = detection_result.get('score') == 1.0
        formatting_passed = formatting_result.get('score') == 1.0
        
        # Special case: broken date format should fail formatting but may pass detection
        if test_case["outputs"]["event_date"] == "PM":
            expected_detection = 1.0 if not should_detect_multi else 0.0  # Single instance detection should work
            expected_formatting = 0.0  # Formatting should fail
        else:
            expected_detection = 1.0
            expected_formatting = 1.0
        
        test_passed = (
            detection_result.get('score') == expected_detection and 
            formatting_result.get('score') == expected_formatting
        )
        
        if test_passed:
            print(f"✅ PASS: Both evaluators working correctly")
        else:
            print(f"❌ FAIL:")
            if detection_result.get('score') != expected_detection:
                print(f"  - Detection score: {detection_result.get('score')} (expected: {expected_detection})")
            if formatting_result.get('score') != expected_formatting:
                print(f"  - Formatting score: {formatting_result.get('score')} (expected: {expected_formatting})")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All evaluation tests PASSED!")
        print("\n🚀 Fixes Applied:")
        print("- Multi-date string parsing: ✅ Comma-separated dates properly split")
        print("- ISO 8601 validation: ✅ Space-separated datetime format supported")
        print("- Detection logic: ✅ Uses total_sessions and comma detection")
        print("- Edge cases: ✅ Handles broken formats appropriately")
    else:
        print("❌ Some evaluation tests FAILED. Framework may still have issues.")
    
    return all_passed

if __name__ == "__main__":
    test_evaluation_fixes()