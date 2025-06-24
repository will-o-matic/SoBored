#!/usr/bin/env python3
"""
Setup script for LangSmith evaluation infrastructure

This script initializes the evaluation system for comparing ReAct agent vs Smart Pipeline
"""

import os
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main setup function"""
    print("🔧 Setting up LangSmith Evaluation Infrastructure")
    print("=" * 60)
    
    # Check environment setup
    print("\n1. Checking Environment Setup")
    print("-" * 30)
    
    env_status = check_environment()
    if not env_status["all_good"]:
        print("❌ Environment setup incomplete. Please fix the issues above.")
        return False
    
    # Initialize evaluation components
    print("\n2. Initializing Evaluation Components")
    print("-" * 40)
    
    try:
        from langgraph.evaluation.langsmith_setup import LangSmithEvaluationSetup
        from langgraph.evaluation.annotation_manager import AnnotationQueueManager
        from langgraph.evaluation.comparison_framework import BeforeAfterComparison
        
        # Initialize components
        setup = LangSmithEvaluationSetup()
        annotation_manager = AnnotationQueueManager(setup.client)
        comparison_framework = BeforeAfterComparison(setup.client)
        
        print("✅ Evaluation components initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize evaluation components: {e}")
        return False
    
    # Setup annotation queue
    print("\n3. Setting up Annotation Queue")
    print("-" * 35)
    
    queue_id = setup.create_event_annotation_queue()
    if queue_id:
        print("✅ Event annotation queue configuration prepared")
        print("📝 Note: Complete setup in LangSmith web interface")
    else:
        print("⚠️  Annotation queue setup requires manual configuration")
    
    # Create evaluation datasets
    print("\n4. Creating Evaluation Datasets")
    print("-" * 35)
    
    datasets_created = create_evaluation_datasets(setup)
    print(f"✅ {datasets_created} evaluation datasets prepared")
    
    # Setup comparison experiment
    print("\n5. Setting up Comparison Experiment")
    print("-" * 40)
    
    experiment_id = setup_comparison_experiment(comparison_framework)
    if experiment_id:
        print(f"✅ Comparison experiment created: {experiment_id}")
    
    # Generate setup report
    print("\n6. Setup Status Report")
    print("-" * 25)
    
    status = setup.get_setup_status()
    print_setup_status(status)
    
    # Print next steps
    print("\n🎯 Next Steps")
    print("-" * 15)
    print_next_steps()
    
    print("\n🎉 LangSmith evaluation infrastructure setup completed!")
    return True

def check_environment() -> Dict[str, Any]:
    """Check if environment is properly configured"""
    status = {"all_good": True, "issues": []}
    
    # Check LangSmith API key
    if not os.environ.get("LANGSMITH_API_KEY"):
        print("⚠️  LANGSMITH_API_KEY not set in environment")
        status["issues"].append("Missing LANGSMITH_API_KEY")
        status["all_good"] = False
    else:
        print("✅ LANGSMITH_API_KEY configured")
    
    # Check Anthropic API key (for smart pipeline)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set (needed for smart pipeline)")
        status["issues"].append("Missing ANTHROPIC_API_KEY")
        status["all_good"] = False
    else:
        print("✅ ANTHROPIC_API_KEY configured")
    
    # Check if langsmith package is installed
    try:
        import langsmith
        print("✅ LangSmith package installed")
    except ImportError:
        print("❌ LangSmith package not installed")
        print("   Run: pip install langsmith")
        status["issues"].append("LangSmith package not installed")
        status["all_good"] = False
    
    # Check project structure
    required_dirs = [
        "langgraph/evaluation",
        "langgraph/pipeline", 
        "langgraph/agents"
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} directory exists")
        else:
            print(f"❌ {dir_path} directory missing")
            status["issues"].append(f"Missing {dir_path}")
            status["all_good"] = False
    
    return status

def create_evaluation_datasets(setup) -> int:
    """Create evaluation datasets"""
    datasets = [
        {
            "name": "event_extraction_baseline",
            "description": "Baseline performance data from ReAct agent system"
        },
        {
            "name": "event_extraction_gold_standard", 
            "description": "Manually curated high-quality event extractions for evaluation"
        },
        {
            "name": "pipeline_comparison_test_set",
            "description": "Test cases for comparing ReAct agent vs Smart Pipeline"
        },
        {
            "name": "edge_cases_collection",
            "description": "Challenging edge cases for system robustness testing"
        }
    ]
    
    created_count = 0
    for dataset_config in datasets:
        try:
            dataset_id = setup.create_evaluation_dataset(
                dataset_config["name"],
                dataset_config["description"]
            )
            if dataset_id:
                created_count += 1
                print(f"✅ Created dataset: {dataset_config['name']}")
            else:
                print(f"⚠️  Dataset creation prepared: {dataset_config['name']}")
                created_count += 1  # Count as prepared
        except Exception as e:
            print(f"❌ Failed to create dataset {dataset_config['name']}: {e}")
    
    return created_count

def setup_comparison_experiment(comparison_framework) -> str:
    """Setup initial comparison experiment"""
    try:
        experiment_id = comparison_framework.create_comparison_experiment(
            experiment_name="react_agent_vs_smart_pipeline",
            baseline_system="react_agent",
            new_system="smart_pipeline"
        )
        
        # Add sample test cases
        test_cases = [
            {
                "input": "https://www.a2sf.org/events/david-zinn-chalk-art/",
                "description": "Real event URL from trace analysis",
                "expected_type": "url"
            },
            {
                "input": "Concert tonight at 8PM downtown at The Venue",
                "description": "Text with clear event details",
                "expected_type": "text"
            },
            {
                "input": "Workshop on machine learning this Saturday at 2PM, room 101",
                "description": "Educational event with time and location",
                "expected_type": "text"
            },
            {
                "input": "https://eventbrite.com/e/sample-event-123456",
                "description": "Eventbrite URL format",
                "expected_type": "url"
            }
        ]
        
        comparison_framework.add_test_cases(experiment_id, test_cases)
        return experiment_id
        
    except Exception as e:
        print(f"❌ Failed to setup comparison experiment: {e}")
        return None

def print_setup_status(status: Dict[str, Any]):
    """Print setup status information"""
    print(f"LangSmith Client: {'✅ Available' if status['langsmith_client_available'] else '❌ Not available'}")
    print(f"API Key Configured: {'✅ Yes' if status['api_key_configured'] else '❌ No'}")
    print(f"Setup Time: {status['setup_timestamp']}")

def print_next_steps():
    """Print next steps for completing setup"""
    steps = [
        "1. 🌐 Open LangSmith web interface (https://smith.langchain.com)",
        "2. 📋 Create annotation queue using provided rubric configuration",
        "3. ⚙️  Set up automated rules for queue population",
        "4. 👥 Configure team access and reviewer permissions",
        "5. 🧪 Run initial comparison experiment:",
        "   python run_comparison_experiment.py",
        "6. 📊 Review results and feedback in LangSmith dashboard",
        "7. 🚀 Enable smart pipeline with: export USE_SMART_PIPELINE=true"
    ]
    
    for step in steps:
        print(f"   {step}")

def create_sample_comparison_script():
    """Create a sample script for running comparisons"""
    script_content = '''#!/usr/bin/env python3
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
'''
    
    with open("run_comparison_experiment.py", "w") as f:
        f.write(script_content)
    
    print("✅ Created sample comparison script: run_comparison_experiment.py")

if __name__ == "__main__":
    # Create sample comparison script
    create_sample_comparison_script()
    
    # Run main setup
    success = main()
    sys.exit(0 if success else 1)