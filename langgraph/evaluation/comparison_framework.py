"""
Before/after comparison framework for evaluating system improvements
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BeforeAfterComparison:
    """
    Framework for comparing system performance before and after improvements
    """
    
    def __init__(self, langsmith_client=None):
        self.client = langsmith_client
        self.experiments = {}
        
    def create_comparison_experiment(self, experiment_name: str, 
                                   baseline_system: str, new_system: str) -> str:
        """
        Create a new comparison experiment
        
        Args:
            experiment_name: Name for the experiment
            baseline_system: Name of the baseline system (e.g., "react_agent")
            new_system: Name of the new system (e.g., "smart_pipeline")
            
        Returns:
            Experiment ID
        """
        experiment_id = f"{experiment_name}_{int(time.time())}"
        
        self.experiments[experiment_id] = {
            "name": experiment_name,
            "baseline_system": baseline_system,
            "new_system": new_system,
            "created_at": datetime.utcnow(),
            "test_cases": [],
            "results": {
                baseline_system: [],
                new_system: []
            },
            "metrics": {}
        }
        
        logger.info(f"Created comparison experiment: {experiment_name} (ID: {experiment_id})")
        return experiment_id
    
    def add_test_cases(self, experiment_id: str, test_cases: List[Dict[str, Any]]) -> bool:
        """
        Add test cases to an experiment
        
        Args:
            experiment_id: ID of the experiment
            test_cases: List of test case dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
            
        self.experiments[experiment_id]["test_cases"].extend(test_cases)
        logger.info(f"Added {len(test_cases)} test cases to experiment {experiment_id}")
        return True
    
    def run_comparison(self, experiment_id: str, 
                      baseline_processor: Callable, new_processor: Callable) -> Dict[str, Any]:
        """
        Run comparison between baseline and new system
        
        Args:
            experiment_id: ID of the experiment
            baseline_processor: Function to process with baseline system
            new_processor: Function to process with new system
            
        Returns:
            Comparison results
        """
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return {"error": "Experiment not found"}
            
        experiment = self.experiments[experiment_id]
        test_cases = experiment["test_cases"]
        
        if not test_cases:
            logger.error(f"No test cases found for experiment {experiment_id}")
            return {"error": "No test cases available"}
        
        logger.info(f"Running comparison for experiment {experiment_id} with {len(test_cases)} test cases")
        
        baseline_results = []
        new_system_results = []
        
        for i, test_case in enumerate(test_cases):
            logger.debug(f"Processing test case {i+1}/{len(test_cases)}")
            
            # Run baseline system
            try:
                baseline_start = time.time()
                baseline_result = baseline_processor(test_case["input"])
                baseline_time = time.time() - baseline_start
                
                baseline_results.append({
                    "test_case_id": i,
                    "input": test_case["input"],
                    "result": baseline_result,
                    "processing_time": baseline_time,
                    "success": not bool(baseline_result.get("error")),
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Baseline system failed on test case {i}: {e}")
                baseline_results.append({
                    "test_case_id": i,
                    "input": test_case["input"],
                    "error": str(e),
                    "processing_time": 0,
                    "success": False,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Run new system
            try:
                new_start = time.time()
                new_result = new_processor(test_case["input"])
                new_time = time.time() - new_start
                
                new_system_results.append({
                    "test_case_id": i,
                    "input": test_case["input"],
                    "result": new_result,
                    "processing_time": new_time,
                    "success": not bool(new_result.get("error")),
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"New system failed on test case {i}: {e}")
                new_system_results.append({
                    "test_case_id": i,
                    "input": test_case["input"],
                    "error": str(e),
                    "processing_time": 0,
                    "success": False,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Store results
        experiment["results"][experiment["baseline_system"]] = baseline_results
        experiment["results"][experiment["new_system"]] = new_system_results
        
        # Calculate metrics
        metrics = self._calculate_comparison_metrics(baseline_results, new_system_results)
        experiment["metrics"] = metrics
        
        logger.info(f"Comparison completed for experiment {experiment_id}")
        return {
            "experiment_id": experiment_id,
            "test_cases_processed": len(test_cases),
            "metrics": metrics,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_comparison_metrics(self, baseline_results: List[Dict], 
                                    new_results: List[Dict]) -> Dict[str, Any]:
        """
        Calculate comparison metrics between baseline and new system
        
        Args:
            baseline_results: Results from baseline system
            new_results: Results from new system
            
        Returns:
            Dictionary with calculated metrics
        """
        if not baseline_results or not new_results:
            return {"error": "Insufficient data for metrics calculation"}
        
        # Performance metrics
        baseline_times = [r["processing_time"] for r in baseline_results if r["success"]]
        new_times = [r["processing_time"] for r in new_results if r["success"]]
        
        baseline_success_rate = sum(1 for r in baseline_results if r["success"]) / len(baseline_results)
        new_success_rate = sum(1 for r in new_results if r["success"]) / len(new_results)
        
        metrics = {
            "performance": {
                "baseline_avg_time": sum(baseline_times) / len(baseline_times) if baseline_times else 0,
                "new_avg_time": sum(new_times) / len(new_times) if new_times else 0,
                "speedup_factor": 0,
                "baseline_success_rate": baseline_success_rate,
                "new_success_rate": new_success_rate,
                "success_rate_improvement": new_success_rate - baseline_success_rate
            },
            "extraction_quality": {
                "baseline_completeness": 0,  # Would calculate from actual extractions
                "new_completeness": 0,
                "accuracy_comparison": {},
                "field_extraction_rates": {}
            },
            "system_efficiency": {
                "baseline_llm_calls": 0,  # Would extract from results
                "new_llm_calls": 0,
                "resource_usage_reduction": 0,
                "cost_efficiency_improvement": 0
            }
        }
        
        # Calculate speedup factor
        if baseline_times and new_times:
            baseline_avg = sum(baseline_times) / len(baseline_times)
            new_avg = sum(new_times) / len(new_times)
            if new_avg > 0:
                metrics["performance"]["speedup_factor"] = baseline_avg / new_avg
        
        return metrics
    
    def generate_comparison_report(self, experiment_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive comparison report
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            Detailed comparison report
        """
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}
        
        experiment = self.experiments[experiment_id]
        
        report = {
            "experiment_info": {
                "name": experiment["name"],
                "baseline_system": experiment["baseline_system"],
                "new_system": experiment["new_system"],
                "created_at": experiment["created_at"].isoformat(),
                "test_cases_count": len(experiment["test_cases"])
            },
            "executive_summary": self._generate_executive_summary(experiment),
            "detailed_metrics": experiment.get("metrics", {}),
            "recommendations": self._generate_recommendations(experiment),
            "next_steps": [
                "Review detailed metrics for areas of improvement",
                "Analyze failed test cases for system robustness",
                "Consider gradual rollout based on success rate improvements",
                "Setup monitoring for production deployment"
            ]
        }
        
        return report
    
    def _generate_executive_summary(self, experiment: Dict) -> Dict[str, Any]:
        """Generate executive summary of experiment results"""
        metrics = experiment.get("metrics", {})
        performance = metrics.get("performance", {})
        
        speedup = performance.get("speedup_factor", 0)
        success_improvement = performance.get("success_rate_improvement", 0)
        
        summary = {
            "overall_assessment": "improvement" if speedup > 1 or success_improvement > 0 else "needs_work",
            "key_improvements": [],
            "concerns": [],
            "confidence_level": "high" if speedup > 2 and success_improvement >= 0 else "medium"
        }
        
        if speedup > 1:
            summary["key_improvements"].append(f"{speedup:.1f}x performance improvement")
        if success_improvement > 0:
            summary["key_improvements"].append(f"{success_improvement:.1%} higher success rate")
        
        if speedup < 1:
            summary["concerns"].append("Performance regression detected")
        if success_improvement < 0:
            summary["concerns"].append("Success rate decreased")
        
        return summary
    
    def _generate_recommendations(self, experiment: Dict) -> List[str]:
        """Generate recommendations based on experiment results"""
        metrics = experiment.get("metrics", {})
        performance = metrics.get("performance", {})
        
        recommendations = []
        
        speedup = performance.get("speedup_factor", 0)
        if speedup > 2:
            recommendations.append("Strong performance improvement - recommend production rollout")
        elif speedup > 1:
            recommendations.append("Moderate improvement - consider gradual rollout")
        else:
            recommendations.append("Performance needs optimization before production deployment")
        
        success_rate = performance.get("new_success_rate", 0)
        if success_rate < 0.95:
            recommendations.append("Address reliability issues before wider deployment")
        
        recommendations.append("Setup continuous monitoring for production performance")
        recommendations.append("Create feedback loop for ongoing improvements")
        
        return recommendations