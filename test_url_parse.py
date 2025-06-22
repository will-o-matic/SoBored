#!/usr/bin/env python3
"""
URL Parse Test Harness

A specialized test harness for testing the URL parsing flow in the SoBored event aggregator.
This script runs only the URL-specific nodes (classifier -> url_fetcher -> url_parser) 
without persisting to Notion, providing detailed output for debugging and validation.

Usage:
    python test_url_parse.py "https://example.com/event"
    python test_url_parse.py --interactive
    python test_url_parse.py "https://example.com" --verbose
    python test_url_parse.py "https://example.com" --json
"""

import os
import sys
import json
import argparse
import re
from typing import Dict, Any, Optional
from pprint import pprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LangGraph components
from langgraph.graph import StateGraph, START, END
from utils.state import EventState
from langgraph.nodes import classify_input, fetch_url_content, parse_url_content


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def create_url_test_graph():
    """
    Create a LangGraph for testing URL parsing flow only.
    
    This graph excludes Notion saving and focuses only on:
    - Classification of input
    - URL content fetching  
    - URL content parsing
    
    Returns:
        Compiled LangGraph application for URL testing
    """
    print(f"{Colors.HEADER}=' Creating URL test graph...{Colors.ENDC}")
    
    # Create the graph
    graph = StateGraph(EventState)
    
    # Add only URL-relevant nodes
    graph.add_node("classifier", classify_input)
    graph.add_node("url_fetcher", fetch_url_content)
    graph.add_node("url_parser", parse_url_content)
    
    # Set up the flow
    graph.add_edge(START, "classifier")
    
    # Conditional edge: route based on input type
    def route_after_classification(state: EventState) -> str:
        if state.input_type == "url":
            return "url_fetcher"
        else:
            return "END"  # Skip if not a URL
    
    graph.add_conditional_edges("classifier", route_after_classification, {
        "url_fetcher": "url_fetcher",
        "END": END
    })
    
    # Linear flow for URL processing
    graph.add_edge("url_fetcher", "url_parser")
    graph.add_edge("url_parser", END)
    
    print(f"{Colors.OKGREEN} URL test graph created successfully{Colors.ENDC}")
    return graph.compile()


def print_state_section(title: str, state: EventState, fields: list, verbose: bool = False):
    """
    Print a formatted section of the EventState.
    
    Args:
        title: Section title
        state: Current EventState
        fields: List of field names to display
        verbose: Whether to show detailed field descriptions
    """
    print(f"\n{Colors.BOLD}{Colors.UNDERLINE}{title}{Colors.ENDC}")
    print("-" * len(title))
    
    for field in fields:
        # Handle both EventState objects and dictionary-like objects
        if hasattr(state, field):
            value = getattr(state, field, None)
        else:
            value = state.get(field, None) if hasattr(state, 'get') else None
            
        if value is not None:
            # Format different types appropriately
            if isinstance(value, str) and len(value) > 100 and not verbose:
                display_value = value[:100] + "..."
            else:
                display_value = value
            
            print(f"{Colors.OKCYAN}{field}:{Colors.ENDC} {display_value}")
        elif verbose:
            print(f"{Colors.WARNING}{field}:{Colors.ENDC} None")


def dump_full_state(state: EventState, verbose: bool = False):
    """
    Display the complete EventState in a formatted way.
    
    Args:
        state: EventState to display
        verbose: Whether to show all fields including None values
    """
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}COMPLETE EVENT STATE{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    # Input & Classification
    print_state_section("=� INPUT & CLASSIFICATION", state, [
        "raw_input", "source", "input_type", "error"
    ], verbose)
    
    # Webpage Fetching
    print_state_section("< WEBPAGE FETCHING", state, [
        "fetch_status", "fetch_error", "webpage_title", "webpage_content"
    ], verbose)
    
    # Event Parsing
    print_state_section("<� EVENT PARSING", state, [
        "event_title", "event_date", "event_location", "event_description", "parsing_confidence"
    ], verbose)
    
    # Response (if any)
    print_state_section("=� RESPONSE", state, [
        "response_message"
    ], verbose)
    
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def test_url_parse(url: str, verbose: bool = False, json_output: bool = False) -> Dict[str, Any]:
    """
    Test the URL parsing flow with a specific URL.
    
    Args:
        url: URL to test
        verbose: Whether to show detailed output
        json_output: Whether to output results as JSON
        
    Returns:
        Dict containing test results
    """
    if not json_output:
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}>� TESTING URL PARSE FLOW{Colors.ENDC}")
        print(f"{Colors.BOLD}URL: {url}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    try:
        # Create the test graph
        app = create_url_test_graph()
        
        # Create initial state
        initial_state = EventState(
            raw_input=url,
            source="test_harness"
        )
        
        if not json_output:
            print(f"\n{Colors.OKBLUE}=� Initial State:{Colors.ENDC}")
            print(f"Raw Input: {url}")
            print(f"Source: test_harness")
        
        # Execute the graph and capture intermediate states
        if not json_output:
            print(f"\n{Colors.OKBLUE}Executing URL parse flow...{Colors.ENDC}")
            
            # Check execution environment and dependencies
            print(f"\n{Colors.OKCYAN}Environment Check:{Colors.ENDC}")
            print(f"Execution context: {'Claude Code session' if any(['claude' in str(type(obj)).lower() for obj in globals().values()]) else 'Standalone Python script'}")
            print(f"Python executable: {sys.executable}")
            print(f"Working directory: {os.getcwd()}")
            
            print(f"\n{Colors.OKCYAN}Dependency Check:{Colors.ENDC}")
            try:
                import requests
                print(f"✓ requests module available")
            except ImportError:
                print(f"✗ requests module missing")
            
            try:
                import bs4
                print(f"✓ beautifulsoup4 (bs4) module available")
            except ImportError:
                print(f"✗ beautifulsoup4 (bs4) module missing")
            
            # Check for MCP fetch availability (multiple possible ways)
            mcp_available = False
            mcp_methods = []
            
            try:
                from mcp import fetch
                mcp_available = True
                mcp_methods.append("importable module")
            except ImportError:
                pass
            
            if 'mcp__fetch__fetch' in globals():
                mcp_available = True
                mcp_methods.append("global function")
            
            # Check if we're in a Claude Code environment
            claude_code_indicators = [
                'mcp__fetch__fetch' in dir(),
                any('claude' in str(type(obj)).lower() for obj in globals().values()),
                os.getenv('CLAUDE_CODE_SESSION') is not None
            ]
            
            if mcp_available:
                print(f"✓ MCP fetch available ({', '.join(mcp_methods)})")
            else:
                print(f"✗ MCP fetch not available")
                if any(claude_code_indicators):
                    print(f"  ℹ️  Running in Claude Code but MCP not detected")
                else:
                    print(f"  ℹ️  Running standalone (MCP only available in Claude Code sessions)")
                print(f"  → Using requests + beautifulsoup4 fallback")
            
            # Test basic connectivity
            try:
                import urllib.request
                import socket
                socket.setdefaulttimeout(5)
                with urllib.request.urlopen("https://httpbin.org/status/200") as response:
                    if response.getcode() == 200:
                        print(f"✓ Basic HTTP connectivity working")
                    else:
                        print(f"✗ HTTP connectivity issues (status: {response.getcode()})")
            except Exception as e:
                print(f"✗ HTTP connectivity test failed: {str(e)[:50]}...")
        
        # Run the complete graph
        final_state = app.invoke(initial_state)
        
        if not json_output:
            # Display results
            if final_state.get('input_type') != "url":
                print(f"\n{Colors.WARNING}�  Input was not classified as URL!{Colors.ENDC}")
                print(f"Classified as: {final_state.get('input_type', 'unknown')}")
                dump_full_state(final_state, verbose)
                return {"error": "Input not classified as URL", "state": dict(final_state)}
            
            # Show fetch results
            print(f"\n{Colors.OKGREEN}< Webpage Fetch Results:{Colors.ENDC}")
            print(f"Status: {final_state.get('fetch_status')}")
            if final_state.get('fetch_error'):
                error_msg = final_state.get('fetch_error')
                print(f"{Colors.FAIL}Error: {error_msg}{Colors.ENDC}")
                
                # Provide helpful troubleshooting info
                if "No module named 'bs4'" in str(error_msg):
                    print(f"\n{Colors.WARNING}Fix: Install missing dependencies:{Colors.ENDC}")
                    print(f"   pip install requests beautifulsoup4")
                elif "No module named 'requests'" in str(error_msg):
                    print(f"\n{Colors.WARNING}Fix: Install missing dependencies:{Colors.ENDC}")
                    print(f"   pip install requests beautifulsoup4")
                elif "No module named 'mcp'" in str(error_msg):
                    print(f"\n{Colors.WARNING}Note: MCP not available, using fallback{Colors.ENDC}")
            if final_state.get('webpage_title'):
                print(f"Title: {final_state.get('webpage_title')}")
            if final_state.get('webpage_content'):
                webpage_content = final_state.get('webpage_content', '')
                content_preview = webpage_content[:200] + "..." if len(webpage_content) > 200 else webpage_content
                print(f"Content (preview): {content_preview}")
            elif final_state.get('fetch_status') == 'success':
                print(f"{Colors.WARNING}Warning: Fetch succeeded but no content retrieved{Colors.ENDC}")
            
            # Show parsing results
            print(f"\n{Colors.OKGREEN}<� Event Parsing Results:{Colors.ENDC}")
            if final_state.get('parsing_confidence') is not None:
                confidence = final_state.get('parsing_confidence', 0)
                confidence_color = Colors.OKGREEN if confidence > 0.7 else Colors.WARNING if confidence > 0.4 else Colors.FAIL
                print(f"Confidence: {confidence_color}{confidence:.2f}{Colors.ENDC}")
            
            if final_state.get('event_title'):
                print(f"Event Title: {final_state.get('event_title')}")
            if final_state.get('event_date'):
                print(f"Event Date: {final_state.get('event_date')}")
            if final_state.get('event_location'):
                print(f"Event Location: {final_state.get('event_location')}")
            if final_state.get('event_description'):
                print(f"Event Description: {final_state.get('event_description')}")
            
            # Show full state if verbose
            if verbose:
                dump_full_state(final_state, verbose=True)
        
        # Prepare return data
        result = {
            "success": True,
            "url": url,
            "classification": final_state.get('input_type'),
            "fetch_status": final_state.get('fetch_status'),
            "parsing_confidence": final_state.get('parsing_confidence'),
            "parsed_event": {
                "title": final_state.get('event_title'),
                "date": final_state.get('event_date'),
                "location": final_state.get('event_location'),
                "description": final_state.get('event_description')
            },
            "full_state": dict(final_state) if verbose else None
        }
        
        if json_output:
            print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        error_msg = f"Test failed: {str(e)}"
        if not json_output:
            print(f"\n{Colors.FAIL}L {error_msg}{Colors.ENDC}")
        
        result = {"success": False, "error": error_msg, "url": url}
        if json_output:
            print(json.dumps(result, indent=2))
        
        return result


def interactive_mode(verbose: bool = False):
    """
    Interactive mode for testing multiple URLs.
    
    Args:
        verbose: Whether to show detailed output
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}<� INTERACTIVE URL PARSE TESTING{Colors.ENDC}")
    print("Enter URLs to test (or 'quit' to exit)")
    print(f"{Colors.OKCYAN}Tip: Use 'verbose on/off' to toggle detailed output{Colors.ENDC}")
    print("-" * 50)
    
    while True:
        try:
            url = input(f"\n{Colors.BOLD}Enter URL: {Colors.ENDC}").strip()
            
            if url.lower() in ['quit', 'exit', 'q']:
                print(f"{Colors.OKGREEN}=K Goodbye!{Colors.ENDC}")
                break
            
            if url.lower() == 'verbose on':
                verbose = True
                print(f"{Colors.OKGREEN} Verbose mode enabled{Colors.ENDC}")
                continue
            elif url.lower() == 'verbose off':
                verbose = False
                print(f"{Colors.OKGREEN} Verbose mode disabled{Colors.ENDC}")
                continue
            
            if not url:
                continue
            
            # Validate URL format
            if not re.match(r'https?://', url):
                print(f"{Colors.WARNING}�  Adding https:// prefix to URL{Colors.ENDC}")
                url = "https://" + url
            
            # Test the URL
            test_url_parse(url, verbose=verbose)
            
        except KeyboardInterrupt:
            print(f"\n{Colors.OKGREEN}=K Goodbye!{Colors.ENDC}")
            break
        except Exception as e:
            print(f"{Colors.FAIL}L Error: {e}{Colors.ENDC}")


def validate_url(url: str) -> str:
    """
    Validate and normalize URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        Normalized URL
        
    Raises:
        ValueError: If URL is invalid
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Add protocol if missing
    if not re.match(r'https?://', url):
        url = "https://" + url
    
    # Basic URL validation
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?)?'
    if not re.match(url_pattern, url):
        raise ValueError(f"Invalid URL format: {url}")
    
    return url


def main():
    """Main CLI interface for URL parse testing."""
    parser = argparse.ArgumentParser(
        description="Test harness for URL parsing flow in SoBored event aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_url_parse.py "https://eventbrite.com/some-event"
  python test_url_parse.py "https://example.com" --verbose
  python test_url_parse.py --interactive
  python test_url_parse.py "https://example.com" --json
  
Environment:
  Requires ANTHROPIC_API_KEY in .env file for Claude API access.
        """
    )
    
    parser.add_argument(
        'url', 
        nargs='?', 
        help='URL to test (required unless --interactive is used)'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode for testing multiple URLs'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output including full state dump'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results as JSON (useful for scripting)'
    )
    
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print(f"{Colors.FAIL}L ANTHROPIC_API_KEY not found in environment{Colors.ENDC}")
        print("Add your Claude API key to the .env file:")
        print("ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)
    
    if args.interactive:
        interactive_mode(verbose=args.verbose)
    elif args.url:
        try:
            validated_url = validate_url(args.url)
            test_url_parse(validated_url, verbose=args.verbose, json_output=args.json)
        except ValueError as e:
            print(f"{Colors.FAIL}L {e}{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"{Colors.FAIL}L Please provide a URL or use --interactive mode{Colors.ENDC}")
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()