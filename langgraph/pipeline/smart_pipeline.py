"""
Smart Event Processing Pipeline

Main pipeline router that coordinates classification and specialized processing
"""

import logging
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime
from langsmith import traceable
from langsmith.run_trees import RunTree
from .classifiers.smart_classifier import SmartClassifier
from .processors.url_processor import URLProcessor
from .processors.text_processor import TextProcessor
from .processors.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class SmartEventPipeline:
    """
    Smart pipeline for event extraction with optimized performance
    
    Features:
    - 3-tier smart classification
    - Specialized processors for different input types
    - Feature flag support for gradual rollout
    - Enhanced LangSmith integration
    - Performance monitoring and statistics
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.classifier = SmartClassifier(use_llm_fallback=True)
        self.processors = {
            "url": URLProcessor(dry_run=dry_run),
            "text": TextProcessor(dry_run=dry_run),
            "email": TextProcessor(dry_run=dry_run),  # Treat emails as text for now
            "image": ImageProcessor(dry_run=dry_run),
        }
        self.pipeline_stats = {
            "total_processed": 0,
            "classification_time": 0.0,
            "processing_time": 0.0,
            "total_time": 0.0,
            "success_count": 0,
            "error_count": 0
        }
    
    def process_event_input(self, raw_input: str, source: str = "telegram", 
                           user_id: Optional[str] = None, telegram_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main entry point for smart pipeline processing with proper LangSmith tracing
        
        Args:
            raw_input: Raw input content (URL, text, etc.)
            source: Source of the input (telegram, web, etc.)
            user_id: Optional user identifier
            telegram_data: Optional Telegram-specific data for image processing
            
        Returns:
            Dict containing complete processing results
        """
        # Create parent RunTree for the entire pipeline
        parent_run = RunTree(
            name="Smart Event Processing Pipeline",
            run_type="chain",
            inputs={
                "raw_input": raw_input,
                "source": source,
                "user_id": user_id,
                "dry_run": self.dry_run
            },
            tags=["smart_pipeline", source, "event_processing"],
            metadata={
                "pipeline_version": "1.0",
                "user_id": user_id,
                "source": source
            }
        )
        parent_run.post()
        
        start_time = time.time()
        classification_start = time.time()
        
        try:
            logger.info(f"Starting smart pipeline processing for input: {raw_input[:100]}...")
            
            # Step 1: Smart Classification (as child run)
            classification_run = parent_run.create_child(
                name="Smart Input Classification",
                run_type="tool",
                inputs={"raw_input": raw_input}
            )
            classification_run.post()
            
            classified_input = self.classifier.classify(raw_input)
            
            # Add telegram_data to classified_input if available (for image processing)
            if telegram_data:
                classified_input["telegram_data"] = telegram_data
            
            classification_time = time.time() - classification_start
            
            classification_run.end(outputs=classified_input)
            classification_run.patch()
            
            logger.debug(f"Classification completed in {classification_time:.3f}s: {classified_input}")
            
            # Step 2: Route to appropriate processor (as child run)
            processing_start = time.time()
            input_type = classified_input.get("input_type", "text")
            
            if input_type not in self.processors:
                logger.warning(f"No processor found for input type: {input_type}, using text processor")
                input_type = "text"
            
            processor_run = parent_run.create_child(
                name=f"{input_type.title()} Event Processing",
                run_type="chain",
                inputs={
                    "classified_input": classified_input,
                    "processor_type": input_type
                }
            )
            processor_run.post()
            
            processor = self.processors[input_type]
            processing_result = processor.process(classified_input, source, user_id, processor_run)
            processing_time = time.time() - processing_start
            
            processor_run.end(outputs=processing_result)
            processor_run.patch()
            
            # Step 3: Combine results with pipeline metadata
            total_time = time.time() - start_time
            
            final_result = {
                **processing_result,
                "pipeline_metadata": {
                    "pipeline_type": "smart_pipeline",
                    "classification_time": classification_time,
                    "processing_time": processing_time,
                    "total_pipeline_time": total_time,
                    "processor_used": input_type,
                    "classification_tier": classified_input.get("method", "unknown"),
                    "dry_run": self.dry_run
                }
            }
            
            # Update statistics
            self._update_pipeline_stats(classification_time, processing_time, total_time, True)
            
            # End parent run successfully
            parent_run.end(outputs=final_result)
            parent_run.patch()
            
            logger.info(f"Smart pipeline processing completed in {total_time:.2f}s")
            return final_result
            
        except Exception as e:
            total_time = time.time() - start_time
            error_result = {
                "error": str(e),
                "processing_status": "pipeline_failed",
                "raw_input": raw_input,
                "source": source,
                "user_id": user_id,
                "pipeline_metadata": {
                    "pipeline_type": "smart_pipeline",
                    "total_pipeline_time": total_time,
                    "error_stage": "pipeline_coordination",
                    "dry_run": self.dry_run
                }
            }
            
            # End parent run with error
            parent_run.end(error=str(e))
            parent_run.patch()
            
            self._update_pipeline_stats(0, 0, total_time, False)
            logger.error(f"Smart pipeline processing failed: {e}")
            return error_result
    
    def _update_pipeline_stats(self, classification_time: float, processing_time: float, 
                              total_time: float, success: bool):
        """Update pipeline statistics"""
        self.pipeline_stats["total_processed"] += 1
        self.pipeline_stats["classification_time"] += classification_time
        self.pipeline_stats["processing_time"] += processing_time
        self.pipeline_stats["total_time"] += total_time
        
        if success:
            self.pipeline_stats["success_count"] += 1
        else:
            self.pipeline_stats["error_count"] += 1
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for the entire pipeline"""
        total = self.pipeline_stats["total_processed"]
        if total == 0:
            return {"message": "No items processed yet"}
        
        # Pipeline-level stats
        pipeline_stats = {
            "pipeline_overview": {
                "total_processed": total,
                "success_rate": (self.pipeline_stats["success_count"] / total) * 100,
                "error_rate": (self.pipeline_stats["error_count"] / total) * 100,
                "avg_total_time": self.pipeline_stats["total_time"] / total,
                "avg_classification_time": self.pipeline_stats["classification_time"] / total,
                "avg_processing_time": self.pipeline_stats["processing_time"] / total
            }
        }
        
        # Classifier stats
        pipeline_stats["classification_stats"] = self.classifier.get_stats()
        
        # Processor stats
        pipeline_stats["processor_stats"] = {}
        for processor_type, processor in self.processors.items():
            pipeline_stats["processor_stats"][processor_type] = processor.get_stats()
        
        return pipeline_stats
    
    def reset_stats(self):
        """Reset all pipeline statistics"""
        self.pipeline_stats = {
            "total_processed": 0,
            "classification_time": 0.0,
            "processing_time": 0.0,
            "total_time": 0.0,
            "success_count": 0,
            "error_count": 0
        }
        
        self.classifier.classification_stats = {
            "tier1_hits": 0,
            "tier2_hits": 0,
            "tier3_hits": 0,
            "total_classifications": 0
        }
        
        for processor in self.processors.values():
            processor.reset_stats()


def create_smart_pipeline(dry_run: bool = False) -> SmartEventPipeline:
    """
    Factory function to create a SmartEventPipeline instance
    
    Args:
        dry_run: Whether to run in dry-run mode (no actual Notion saves)
        
    Returns:
        Configured SmartEventPipeline instance
    """
    return SmartEventPipeline(dry_run=dry_run)


def should_use_smart_pipeline() -> bool:
    """
    Check if smart pipeline should be used based on feature flags
    
    Returns:
        True if smart pipeline should be used, False for ReAct agent fallback
    """
    # Check environment variable feature flag
    use_smart_pipeline = os.getenv("USE_SMART_PIPELINE", "false").lower()
    return use_smart_pipeline in ["true", "1", "yes", "on"]


def process_with_smart_pipeline(raw_input: str, source: str = "telegram", 
                               user_id: Optional[str] = None, dry_run: bool = False,
                               telegram_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Convenience function for processing with smart pipeline
    
    Args:
        raw_input: Raw input content
        source: Source of the input
        user_id: Optional user identifier
        dry_run: Whether to run in dry-run mode
        telegram_data: Optional Telegram-specific data for image processing
        
    Returns:
        Processing results
    """
    pipeline = create_smart_pipeline(dry_run=dry_run)
    return pipeline.process_event_input(raw_input, source, user_id, telegram_data)