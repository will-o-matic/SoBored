"""
Base processor class for event extraction pipeline
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """
    Abstract base class for all event processors
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.processing_stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_processing_time": 0.0
        }
    
    @abstractmethod
    def process(self, classified_input: Dict[str, Any], source: str = "telegram", 
                user_id: Optional[str] = None, parent_run=None) -> Dict[str, Any]:
        """
        Process classified input and extract event data
        
        Args:
            classified_input: Output from SmartClassifier
            source: Source of the input (telegram, web, etc.)
            user_id: Optional user identifier
            
        Returns:
            Dict containing extracted event data and processing metadata
        """
        pass
    
    def _create_base_result(self, classified_input: Dict[str, Any], 
                           source: str, user_id: Optional[str]) -> Dict[str, Any]:
        """Create base result structure with common fields"""
        return {
            "input_type": classified_input.get("input_type"),
            "raw_input": classified_input.get("raw_input"),
            "source": source,
            "user_id": user_id,
            "classification_confidence": classified_input.get("confidence", 0.0),
            "classification_method": classified_input.get("method", "unknown"),
            "processing_timestamp": datetime.utcnow().isoformat(),
            "dry_run": self.dry_run
        }
    
    def _validate_extracted_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and score extracted event data
        
        Args:
            event_data: Extracted event information
            
        Returns:
            Validation results with confidence score
        """
        validation_score = 0.0
        validation_details = {}
        
        # Check for required fields
        required_fields = ["event_title", "event_date", "event_location", "event_description"]
        present_fields = 0
        
        for field in required_fields:
            if field in event_data and event_data[field]:
                present_fields += 1
                validation_details[f"{field}_present"] = True
            else:
                validation_details[f"{field}_present"] = False
        
        # Base score from field presence
        validation_score = present_fields / len(required_fields)
        
        # Quality checks
        if "event_title" in event_data and event_data["event_title"]:
            title = event_data["event_title"]
            if len(title) > 5 and not title.isupper():  # Not all caps spam
                validation_score += 0.1
                
        if "event_date" in event_data and event_data["event_date"]:
            # Basic date format validation
            date_str = str(event_data["event_date"])
            if any(char.isdigit() for char in date_str):
                validation_score += 0.1
                
        if "event_location" in event_data and event_data["event_location"]:
            location = event_data["event_location"]
            if len(location) > 3:  # Not just "TBD" or similar
                validation_score += 0.1
        
        return {
            "validation_score": min(validation_score, 1.0),
            "validation_details": validation_details,
            "quality_indicators": {
                "has_complete_info": present_fields == len(required_fields),
                "field_completion_rate": present_fields / len(required_fields),
                "estimated_accuracy": validation_score
            }
        }
    
    def _update_stats(self, success: bool, processing_time: float):
        """Update processing statistics"""
        self.processing_stats["total_processed"] += 1
        
        if success:
            self.processing_stats["successful_extractions"] += 1
        else:
            self.processing_stats["failed_extractions"] += 1
            
        # Update average processing time
        total = self.processing_stats["total_processed"]
        current_avg = self.processing_stats["average_processing_time"]
        self.processing_stats["average_processing_time"] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        total = self.processing_stats["total_processed"]
        if total == 0:
            return {"message": "No items processed yet"}
            
        return {
            **self.processing_stats,
            "success_rate": (self.processing_stats["successful_extractions"] / total) * 100,
            "failure_rate": (self.processing_stats["failed_extractions"] / total) * 100
        }
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_processing_time": 0.0
        }