#!/usr/bin/env python3
"""
LangSmith Trace Viewer - Utility to fetch and display LangSmith traces for debugging.
"""

import os
import sys
from typing import Optional, Dict, Any
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_langsmith_client():
    """Get configured LangSmith client."""
    try:
        from langsmith import Client
        
        api_key = os.environ.get("LANGSMITH_API_KEY")
        if not api_key:
            print("Error: LANGSMITH_API_KEY not set in environment")
            return None
            
        return Client(
            api_key=api_key,
            api_url=os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        )
    except ImportError:
        print("Error: langsmith package not installed. Run: pip install langsmith")
        return None
    except Exception as e:
        print(f"Error initializing LangSmith client: {e}")
        return None


def fetch_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific trace by ID.
    
    Args:
        trace_id: The LangSmith trace ID
        
    Returns:
        Trace data or None if not found
    """
    client = get_langsmith_client()
    if not client:
        return None
    
    try:
        # Get the trace run
        run = client.read_run(trace_id)
        return run
    except Exception as e:
        print(f"Error fetching trace {trace_id}: {e}")
        return None


def fetch_trace_tree(trace_id: str) -> Optional[list]:
    """
    Fetch complete trace tree including all child runs.
    
    Args:
        trace_id: The LangSmith trace ID
        
    Returns:
        List of runs in the trace tree
    """
    client = get_langsmith_client()
    if not client:
        return None
    
    try:
        # Get all runs in the trace using the correct parameter
        runs = list(client.list_runs(trace=trace_id))
        return runs
    except Exception as e:
        print(f"Error fetching trace tree {trace_id}: {e}")
        return None


def format_run_info(run) -> str:
    """Format run information for display."""
    run_type = getattr(run, 'run_type', 'unknown')
    name = getattr(run, 'name', 'unnamed')
    status = getattr(run, 'status', 'unknown')
    
    # Handle start/end times
    start_time = getattr(run, 'start_time', None)
    end_time = getattr(run, 'end_time', None)
    
    duration = "unknown"
    if start_time and end_time:
        delta = end_time - start_time
        duration = f"{delta.total_seconds():.2f}s"
    
    # Format inputs/outputs
    inputs = getattr(run, 'inputs', {})
    outputs = getattr(run, 'outputs', {})
    error = getattr(run, 'error', None)
    
    result = f"""
Run: {name} ({run_type})
Status: {status}
Duration: {duration}
ID: {run.id}
"""
    
    if inputs:
        result += f"\nInputs:\n{json.dumps(inputs, indent=2, default=str)}"
    
    if outputs:
        result += f"\nOutputs:\n{json.dumps(outputs, indent=2, default=str)}"
    
    if error:
        result += f"\nError:\n{error}"
    
    return result


def display_trace(trace_id: str, show_tree: bool = True) -> None:
    """
    Display trace information in a readable format.
    
    Args:
        trace_id: The LangSmith trace ID
        show_tree: Whether to show the complete trace tree
    """
    print(f"Fetching LangSmith trace: {trace_id}")
    print("=" * 80)
    
    if show_tree:
        runs = fetch_trace_tree(trace_id)
        if not runs:
            print("No trace data found or error occurred")
            return
        
        print(f"Found {len(runs)} runs in trace tree:")
        print()
        
        # Sort by start time if available
        try:
            runs.sort(key=lambda r: getattr(r, 'start_time', datetime.min))
        except:
            pass
        
        for i, run in enumerate(runs, 1):
            print(f"{'='*20} Run {i}/{len(runs)} {'='*20}")
            print(format_run_info(run))
            print()
    else:
        run = fetch_trace(trace_id)
        if not run:
            print("No trace data found or error occurred")
            return
        
        print(format_run_info(run))


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python langsmith_trace_viewer.py <trace_id> [--tree]")
        print("Example: python langsmith_trace_viewer.py 8261f4b2-d514-4d29-86c8-bac3c591c6c4")
        sys.exit(1)
    
    trace_id = sys.argv[1]
    show_tree = "--tree" in sys.argv or "-t" in sys.argv
    
    # Default to showing tree for better debugging
    if len(sys.argv) == 2:
        show_tree = True
    
    display_trace(trace_id, show_tree)


if __name__ == "__main__":
    main()