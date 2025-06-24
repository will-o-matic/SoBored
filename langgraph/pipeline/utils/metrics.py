"""
Performance metrics and monitoring for smart pipeline
"""

import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

class PipelineMetrics:
    """
    Comprehensive metrics collection for pipeline performance monitoring
    """
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_time = datetime.utcnow()
        
    def record_processing_time(self, stage: str, duration: float, success: bool = True):
        """Record processing time for a specific stage"""
        self.metrics[f"{stage}_duration"].append(duration)
        self.metrics[f"{stage}_success"].append(success)
        
    def record_classification_tier(self, tier: str):
        """Record which classification tier was used"""
        self.metrics["classification_tiers"].append(tier)
        
    def record_processor_type(self, processor_type: str):
        """Record which processor was used"""
        self.metrics["processor_types"].append(processor_type)
        
    def get_performance_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        summary = {
            "time_period": f"Last {hours_back} hours",
            "measurement_start": self.start_time.isoformat(),
            "total_processes": len(self.metrics.get("classification_tiers", [])),
        }
        
        # Processing time analysis
        if "total_duration" in self.metrics:
            durations = self.metrics["total_duration"]
            summary["performance"] = {
                "avg_processing_time": sum(durations) / len(durations),
                "min_processing_time": min(durations),
                "max_processing_time": max(durations),
                "p95_processing_time": self._percentile(durations, 95),
                "p99_processing_time": self._percentile(durations, 99)
            }
        
        # Classification tier usage
        if "classification_tiers" in self.metrics:
            tier_counts = defaultdict(int)
            for tier in self.metrics["classification_tiers"]:
                tier_counts[tier] += 1
            summary["classification_efficiency"] = dict(tier_counts)
        
        # Processor usage
        if "processor_types" in self.metrics:
            processor_counts = defaultdict(int)
            for proc_type in self.metrics["processor_types"]:
                processor_counts[proc_type] += 1
            summary["processor_usage"] = dict(processor_counts)
        
        # Success rates
        success_metrics = {}
        for key in self.metrics:
            if key.endswith("_success"):
                stage = key.replace("_success", "")
                successes = self.metrics[key]
                success_rate = (sum(successes) / len(successes)) * 100 if successes else 0
                success_metrics[stage] = success_rate
        summary["success_rates"] = success_metrics
        
        return summary
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external analysis"""
        return dict(self.metrics)
    
    def reset_metrics(self):
        """Reset all collected metrics"""
        self.metrics.clear()
        self.start_time = datetime.utcnow()