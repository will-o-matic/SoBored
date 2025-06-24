#!/usr/bin/env python3
"""
Sample script for running pipeline comparison experiments
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_comparison():
    """Run comparison between ReAct agent and Smart Pipeline"""
    from langgraph.evaluation.comparison_framework import BeforeAfterComparison
    from langgraph.main_agent import process_event_input
    from langgraph.pipeline.smart_pipeline import process_with_smart_pipeline
    
    # Initialize comparison framework
    comparison = BeforeAfterComparison()
    
    # Create experiment
    experiment_id = comparison.create_comparison_experiment(
        "performance_comparison_test",
        "react_agent", 
        "smart_pipeline"
    )
    
    # Define test cases
    test_cases = [
        {"input": "https://www.a2sf.org/events/david-zinn-chalk-art/"},
        {"input": "Concert tonight at 8PM downtown"}
    ]
    
    comparison.add_test_cases(experiment_id, test_cases)
    
    # Define processing functions
    def react_processor(input_text):
        os.environ["USE_SMART_PIPELINE"] = "false"
        return process_event_input(input_text, dry_run=True)
    
    def pipeline_processor(input_text):
        return process_with_smart_pipeline(input_text, dry_run=True)
    
    # Run comparison
    results = comparison.run_comparison(
        experiment_id, 
        react_processor, 
        pipeline_processor
    )
    
    # Generate report
    report = comparison.generate_comparison_report(experiment_id)
    
    print("Comparison Results:")
    print("=" * 40)
    print(f"Speedup Factor: {report['detailed_metrics']['performance']['speedup_factor']:.2f}x")
    print(f"Success Rate Change: {report['detailed_metrics']['performance']['success_rate_improvement']:.1%}")
    
    return results

if __name__ == "__main__":
    run_comparison()
