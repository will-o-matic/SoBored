#!/usr/bin/env python3
"""
Setup script for multi-date event processing evaluation

This script initializes the LangSmith evaluation framework for testing
multi-date event detection and processing capabilities.
"""

import os
import sys
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

def setup_environment():
    """Load environment variables and validate configuration"""
    load_dotenv()
    
    required_vars = [
        "ANTHROPIC_API_KEY",
        "LANGSMITH_API_KEY", 
        "NOTION_TOKEN",
        "NOTION_DATABASE_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please ensure your .env file contains all required API keys")
        return False
    
    print("✅ Environment variables configured")
    return True

def initialize_langsmith_client():
    """Initialize LangSmith client"""
    try:
        from langsmith import Client
        client = Client()
        print("✅ LangSmith client initialized")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize LangSmith client: {e}")
        return None

def create_evaluation_dataset(client):
    """Create the multi-date evaluation dataset"""
    try:
        from langgraph.evaluation.multi_date_evaluator import MultiDateEventEvaluator
        
        evaluator = MultiDateEventEvaluator(client)
        dataset_id = evaluator.create_evaluation_dataset()
        
        if dataset_id:
            print(f"✅ Created evaluation dataset: {dataset_id}")
            return dataset_id
        else:
            print("❌ Failed to create evaluation dataset")
            return None
            
    except Exception as e:
        print(f"❌ Error creating dataset: {e}")
        return None

def test_smart_pipeline_function():
    """Test that the Smart Pipeline function is available"""
    try:
        from langgraph.pipeline.smart_pipeline import SmartEventPipeline
        
        # Initialize pipeline
        pipeline = SmartEventPipeline(dry_run=True)
        
        # Test with simple input
        test_result = pipeline.process_event_input(
            raw_input="Test event on June 25th at 7PM",
            source="evaluation", 
            user_id="test_user"
        )
        
        if test_result and not test_result.get("error"):
            print("✅ Smart Pipeline function is available and working")
            return True
        else:
            print(f"❌ Smart Pipeline test failed: {test_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Smart Pipeline: {e}")
        return False

def run_initial_evaluation(client, dataset_id):
    """Run the first evaluation experiment"""
    try:
        from langgraph.evaluation.multi_date_evaluator import MultiDateEventEvaluator
        from langgraph.pipeline.smart_pipeline import SmartEventPipeline
        
        evaluator = MultiDateEventEvaluator(client)
        pipeline = SmartEventPipeline(dry_run=True)
        
        print("🚀 Running initial multi-date evaluation...")
        print("This will test the Smart Pipeline against our test cases...")
        
        # Define system function for evaluation
        def smart_pipeline_evaluator(raw_input: str, source: str = "telegram", 
                                   user_id: str = "test_user", dry_run: bool = True) -> Dict[str, Any]:
            """Wrapper function for Smart Pipeline evaluation"""
            return pipeline.process_event_input(
                raw_input=raw_input,
                source=source,
                user_id=user_id
            )
        
        # Run comprehensive evaluation
        experiment_name = f"smart_pipeline_multi_date_{int(time.time())}"
        results = evaluator.run_comprehensive_evaluation(
            system_function=smart_pipeline_evaluator,
            experiment_name=experiment_name
        )
        
        if results and not results.get("error"):
            print(f"✅ Evaluation completed successfully: {experiment_name}")
            
            # Generate report
            report = evaluator.generate_evaluation_report(results)
            print("\n" + "="*60)
            print("EVALUATION REPORT")
            print("="*60)
            print(report)
            
            return True
        else:
            print(f"❌ Evaluation failed: {results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")
        return False

def setup_annotation_queue(client):
    """Setup annotation queue for manual review"""
    try:
        print("📋 Setting up annotation queue for manual review...")
        
        # Create annotation queue configuration
        queue_config = {
            "name": "Multi-Date Event Review",
            "description": "Manual review of multi-date event processing accuracy",
            "instruction": """
Please review the multi-date event processing results:

1. **Detection Accuracy**: Did the system correctly identify this as a multi-date vs single-date event?
2. **Date Extraction**: Are all dates properly extracted and formatted?
3. **Series Linking**: For multi-date events, is the series metadata correct?
4. **Title Format**: Does the title properly indicate session information?

Score each aspect from 1-5 and provide overall feedback.
            """.strip()
        }
        
        print(f"✅ Annotation queue configuration ready")
        print("📝 To create the queue, visit: https://smith.langchain.com/annotation-queues")
        print("Use the configuration above to set up manual review process")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up annotation queue: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Setting up Multi-Date Event Evaluation Framework")
    print("="*60)
    
    # Step 1: Environment setup
    if not setup_environment():
        sys.exit(1)
    
    # Step 2: Initialize LangSmith
    client = initialize_langsmith_client()
    if not client:
        sys.exit(1)
    
    # Step 3: Test Smart Pipeline availability
    if not test_smart_pipeline_function():
        print("⚠️  Smart Pipeline not available - continuing with evaluation anyway")
    
    # Step 4: Create evaluation dataset
    dataset_id = create_evaluation_dataset(client)
    if not dataset_id:
        sys.exit(1)
    
    # Step 5: Run initial evaluation
    if not run_initial_evaluation(client, dataset_id):
        print("⚠️  Initial evaluation failed, but dataset is created")
    
    # Step 6: Setup annotation queue
    setup_annotation_queue(client)
    
    print("\n" + "="*60)
    print("🎉 Multi-Date Event Evaluation Setup Complete!")
    print("="*60)
    print("\n📊 Next Steps:")
    print("1. Visit LangSmith dashboard to view evaluation results")
    print("2. Set up annotation queues for manual review")
    print("3. Run periodic evaluations to track improvements")
    print("4. Use insights to enhance multi-date processing")
    
    print(f"\n🔗 LangSmith Dashboard: https://smith.langchain.com")
    print(f"📈 Dataset: multi_date_event_evaluation")

if __name__ == "__main__":
    main()