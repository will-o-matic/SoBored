"""
LangSmith evaluation setup and configuration
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LangSmithEvaluationSetup:
    """
    Setup and configure LangSmith evaluation infrastructure for event extraction
    """
    
    def __init__(self):
        self.client = self._get_langsmith_client()
        
    def _get_langsmith_client(self):
        """Get configured LangSmith client"""
        try:
            from langsmith import Client
            
            api_key = os.environ.get("LANGSMITH_API_KEY")
            if not api_key:
                logger.warning("LANGSMITH_API_KEY not set - some features may not work")
                return None
                
            return Client(
                api_key=api_key,
                api_url=os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
            )
        except ImportError:
            logger.error("langsmith package not installed. Run: pip install langsmith")
            return None
        except Exception as e:
            logger.error(f"Error initializing LangSmith client: {e}")
            return None
    
    def create_event_annotation_queue(self, queue_name: str = "Event Extraction Quality Review") -> Optional[str]:
        """
        Create annotation queue for event extraction review
        
        Args:
            queue_name: Name for the annotation queue
            
        Returns:
            Queue ID if successful, None otherwise
        """
        if not self.client:
            logger.error("LangSmith client not available")
            return None
            
        try:
            # Define the annotation rubric
            rubric = {
                "name": queue_name,
                "description": """
                Review extracted event information for accuracy and completeness.
                
                This queue helps improve our event extraction system by collecting
                structured feedback on the quality of extracted event details.
                """,
                "instructions": """
                Please review the extracted event information for accuracy:
                
                1. **Title Accuracy**: Is the event title correct and complete?
                2. **Date/Time Accuracy**: Is the date and time accurate and properly formatted?
                3. **Location Accuracy**: Is the venue/location properly extracted and complete?
                4. **Description Quality**: Is the description relevant, complete, and useful?
                
                Rate each field and provide an overall quality score. Include specific
                corrections in the comments field when needed.
                """,
                "feedback_schema": [
                    {
                        "key": "title_accuracy",
                        "type": "categorical",
                        "categories": [
                            {"value": "correct", "description": "Title is accurate and complete"},
                            {"value": "partially_correct", "description": "Title is mostly right but has minor issues"},
                            {"value": "incorrect", "description": "Title is wrong or misleading"},
                            {"value": "missing", "description": "Title not extracted when it should have been"}
                        ],
                        "description": "Accuracy of the extracted event title"
                    },
                    {
                        "key": "datetime_accuracy", 
                        "type": "categorical",
                        "categories": [
                            {"value": "correct", "description": "Date and time are completely accurate"},
                            {"value": "partially_correct", "description": "Date or time has minor issues"},
                            {"value": "incorrect", "description": "Date/time is wrong"},
                            {"value": "missing", "description": "Date/time not extracted when available"}
                        ],
                        "description": "Accuracy of the extracted date and time"
                    },
                    {
                        "key": "location_accuracy",
                        "type": "categorical", 
                        "categories": [
                            {"value": "correct", "description": "Location is accurate and complete"},
                            {"value": "partially_correct", "description": "Location is mostly right but incomplete"},
                            {"value": "incorrect", "description": "Location is wrong"},
                            {"value": "missing", "description": "Location not extracted when available"}
                        ],
                        "description": "Accuracy of the extracted location/venue"
                    },
                    {
                        "key": "description_quality",
                        "type": "categorical",
                        "categories": [
                            {"value": "excellent", "description": "Description is comprehensive and useful"},
                            {"value": "good", "description": "Description is adequate and relevant"},
                            {"value": "poor", "description": "Description is inadequate or irrelevant"},
                            {"value": "missing", "description": "No description when one should exist"}
                        ],
                        "description": "Quality and relevance of the event description"
                    },
                    {
                        "key": "overall_quality",
                        "type": "rating",
                        "min": 1,
                        "max": 5,
                        "description": "Overall extraction quality (1=very poor, 5=excellent)"
                    },
                    {
                        "key": "corrections_needed",
                        "type": "text",
                        "description": "Specific corrections or improvements needed (be detailed)"
                    },
                    {
                        "key": "extraction_confidence",
                        "type": "rating", 
                        "min": 1,
                        "max": 5,
                        "description": "How confident are you in this assessment? (1=uncertain, 5=very confident)"
                    }
                ],
                "reviewer_settings": {
                    "reviewers_per_run": 1,  # Start with single reviewer
                    "enable_reservations": True,
                    "reservation_length_minutes": 30
                }
            }
            
            # Note: The actual LangSmith API for creating annotation queues may differ
            # This is a conceptual implementation - actual API calls would need to be updated
            logger.info(f"Annotation queue configuration prepared: {queue_name}")
            logger.info("To create this queue, use the LangSmith web interface with the provided rubric")
            
            return "manual_setup_required"  # Placeholder - actual implementation would return queue ID
            
        except Exception as e:
            logger.error(f"Failed to create annotation queue: {e}")
            return None
    
    def create_evaluation_dataset(self, dataset_name: str, description: str = None) -> Optional[str]:
        """
        Create a dataset for evaluation
        
        Args:
            dataset_name: Name for the dataset
            description: Optional description
            
        Returns:
            Dataset ID if successful, None otherwise
        """
        if not self.client:
            logger.error("LangSmith client not available")
            return None
            
        try:
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description or f"Event extraction evaluation dataset - {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            logger.info(f"Created evaluation dataset: {dataset_name} (ID: {dataset.id})")
            return dataset.id
            
        except Exception as e:
            logger.error(f"Failed to create evaluation dataset: {e}")
            return None
    
    def add_examples_to_dataset(self, dataset_id: str, examples: List[Dict[str, Any]]) -> bool:
        """
        Add examples to an evaluation dataset
        
        Args:
            dataset_id: ID of the dataset
            examples: List of example dictionaries with 'inputs' and 'outputs'
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("LangSmith client not available")
            return False
            
        try:
            for example in examples:
                self.client.create_example(
                    dataset_id=dataset_id,
                    inputs=example["inputs"],
                    outputs=example.get("outputs", {})
                )
            
            logger.info(f"Added {len(examples)} examples to dataset {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add examples to dataset: {e}")
            return False
    
    def setup_automated_rules(self) -> bool:
        """
        Setup automated rules for populating annotation queues
        
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("LangSmith client not available")
            return False
            
        try:
            # Rule configurations (conceptual - actual API may differ)
            rules = [
                {
                    "name": "queue_all_event_extractions",
                    "description": "Add all event processing runs to review queue",
                    "condition": "run.name == 'process_event_input'",
                    "action": "add_to_annotation_queue",
                    "target_queue": "Event Extraction Quality Review"
                },
                {
                    "name": "priority_low_confidence",
                    "description": "Priority review for low confidence extractions",
                    "condition": "run.outputs.parsing_confidence < 0.7",
                    "action": "add_to_annotation_queue", 
                    "target_queue": "Urgent Review Queue"
                },
                {
                    "name": "build_training_dataset",
                    "description": "Add high-quality reviews to training dataset",
                    "condition": "feedback.overall_quality >= 4",
                    "action": "add_to_dataset",
                    "target_dataset": "high_quality_extractions"
                }
            ]
            
            logger.info("Automated rule configurations prepared")
            logger.info("Rules need to be set up through LangSmith web interface:")
            for rule in rules:
                logger.info(f"  - {rule['name']}: {rule['description']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup automated rules: {e}")
            return False
    
    def get_setup_status(self) -> Dict[str, Any]:
        """
        Get the current setup status
        
        Returns:
            Dictionary with setup status information
        """
        return {
            "langsmith_client_available": self.client is not None,
            "api_key_configured": bool(os.environ.get("LANGSMITH_API_KEY")),
            "setup_timestamp": datetime.utcnow().isoformat(),
            "next_steps": [
                "Create annotation queue in LangSmith web UI using provided rubric",
                "Set up automated rules for queue population", 
                "Create evaluation datasets for before/after comparison",
                "Configure team access and reviewer permissions"
            ]
        }