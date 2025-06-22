#!/usr/bin/env python3
"""
SoBored Agent Flow Test Harness

A comprehensive test harness for the ReAct agent-based event processing system.
Tests the complete pipeline from input classification to Notion saving with 
detailed output for debugging and validation.

Usage:
    python test_url_parse.py "https://example.com/event"
    python test_url_parse.py "Concert tonight at 8pm at Central Park"
    python test_url_parse.py --interactive
    python test_url_parse.py "Meeting tomorrow 2pm" --verbose
    python test_url_parse.py "https://example.com" --json
"""

import os
import sys
import json
import argparse
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the new agent system
try:
    from langgraph.main_agent import process_event_input, create_event_processor
    AGENT_AVAILABLE = True
    AGENT_ERROR = None
except ImportError as e:
    AGENT_AVAILABLE = False
    AGENT_ERROR = str(e)


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


def print_section(title: str, content: Any = None, color: str = Colors.OKBLUE):
    """Print a formatted section with optional content."""
    print(f"\n{color}{Colors.BOLD}{title}{Colors.ENDC}")
    print("-" * len(title))
    if content is not None:
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"{Colors.OKCYAN}{key}:{Colors.ENDC} {value}")
        elif isinstance(content, list):
            for i, item in enumerate(content, 1):
                print(f"{Colors.OKCYAN}{i}.{Colors.ENDC} {item}")
        else:
            print(content)


def check_environment() -> Dict[str, Any]:
    """Check environment setup and dependencies."""
    env_status = {}
    
    # Check required environment variables
    required_vars = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "NOTION_TOKEN": os.getenv("NOTION_TOKEN"),
        "NOTION_DATABASE_ID": os.getenv("NOTION_DATABASE_ID")
    }
    
    env_status["environment_variables"] = {}
    for var_name, var_value in required_vars.items():
        env_status["environment_variables"][var_name] = "✓ Set" if var_value else "✗ Missing"
    
    # Check Python dependencies
    deps_to_check = [
        ("langchain", "langchain"),
        ("langchain_anthropic", "langchain-anthropic"), 
        ("langchain_mcp", "langchain-mcp-adapters"),
        ("anthropic", "anthropic"),
        ("requests", "requests"),
        ("bs4", "beautifulsoup4"),
        ("notion_client", "notion-client"),
        ("fastapi", "fastapi"),
        ("telegram", "python-telegram-bot")
    ]
    
    env_status["dependencies"] = {}
    for import_name, package_name in deps_to_check:
        try:
            __import__(import_name)
            env_status["dependencies"][package_name] = "✓ Available"
        except ImportError:
            env_status["dependencies"][package_name] = "✗ Missing"
    
    # Check agent system availability
    env_status["agent_system"] = "✓ Available" if AGENT_AVAILABLE else f"✗ Error: {AGENT_ERROR}"
    
    return env_status


def test_agent_flow(
    raw_input: str,
    source: str = "test_harness", 
    input_type: Optional[str] = None,
    verbose: bool = False,
    json_output: bool = False
) -> Dict[str, Any]:
    """
    Test the ReAct agent-based event processing flow.
    
    Args:
        raw_input: Input content to process
        source: Source of the input
        input_type: Pre-classified input type (optional)
        verbose: Whether to show detailed output
        json_output: Whether to output results as JSON
        
    Returns:
        Dict containing test results
    """
    if not json_output:
        print(f"\n{Colors.BOLD}{Colors.HEADER}🤖 TESTING REACT AGENT FLOW{Colors.ENDC}")
        print(f"{Colors.BOLD}Input:{Colors.ENDC} {raw_input}")
        print(f"{Colors.BOLD}Source:{Colors.ENDC} {source}")
        if input_type:
            print(f"{Colors.BOLD}Pre-classified Type:{Colors.ENDC} {input_type}")
        print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
    
    # Check if agent system is available
    if not AGENT_AVAILABLE:
        error_msg = f"Agent system not available: {AGENT_ERROR}"
        if not json_output:
            print_section("❌ SYSTEM ERROR", error_msg, Colors.FAIL)
        
        result = {"success": False, "error": error_msg, "input": raw_input}
        if json_output:
            print(json.dumps(result, indent=2))
        return result
    
    try:
        # Environment check
        if not json_output and verbose:
            env_status = check_environment()
            print_section("🔧 ENVIRONMENT CHECK", color=Colors.OKCYAN)
            
            print(f"\n{Colors.BOLD}Environment Variables:{Colors.ENDC}")
            for var, status in env_status["environment_variables"].items():
                color = Colors.OKGREEN if "✓" in status else Colors.FAIL
                print(f"  {color}{status}{Colors.ENDC} {var}")
            
            print(f"\n{Colors.BOLD}Dependencies:{Colors.ENDC}")
            for dep, status in env_status["dependencies"].items():
                color = Colors.OKGREEN if "✓" in status else Colors.WARNING
                print(f"  {color}{status}{Colors.ENDC} {dep}")
            
            print(f"\n{Colors.BOLD}Agent System:{Colors.ENDC}")
            agent_color = Colors.OKGREEN if "✓" in env_status["agent_system"] else Colors.FAIL
            print(f"  {agent_color}{env_status['agent_system']}{Colors.ENDC}")
        
        # Process using the ReAct agent system
        if not json_output:
            print_section("🚀 PROCESSING WITH REACT AGENT", color=Colors.OKBLUE)
            print("Initializing agent and processing input...")
        
        # Call the main agent processing function
        result = process_event_input(
            raw_input=raw_input,
            source=source,
            input_type=input_type
        )
        
        if not json_output:
            # Display results
            if result.get("success"):
                print_section("✅ AGENT EXECUTION SUCCESSFUL", color=Colors.OKGREEN)
                
                # Show agent output
                agent_output = result.get("agent_output", "No output provided")
                print(f"\n{Colors.BOLD}Agent Response:{Colors.ENDC}")
                print(agent_output)
                
                # Parse and display key information from agent output
                if "notion" in agent_output.lower():
                    print_section("📝 NOTION INTEGRATION STATUS", color=Colors.OKCYAN)
                    if any(word in agent_output.lower() for word in ["success", "saved", "created"]):
                        print(f"{Colors.OKGREEN}✓ Event successfully saved to Notion{Colors.ENDC}")
                    elif any(word in agent_output.lower() for word in ["failed", "error", "could not"]):
                        print(f"{Colors.FAIL}✗ Failed to save to Notion{Colors.ENDC}")
                    else:
                        print(f"{Colors.WARNING}? Notion save status unclear{Colors.ENDC}")
                
                # Show reasoning steps if available and verbose
                if verbose and result.get("reasoning_steps"):
                    print_section("🧠 AGENT REASONING STEPS", color=Colors.OKCYAN)
                    for i, step in enumerate(result["reasoning_steps"], 1):
                        print(f"\n{Colors.BOLD}Step {i}:{Colors.ENDC}")
                        print(f"  {Colors.OKCYAN}Action:{Colors.ENDC} {step.get('action', 'Unknown')}")
                        
                        step_input = step.get('input', 'None')
                        if len(str(step_input)) > 150:
                            step_input = str(step_input)[:150] + "..."
                        print(f"  {Colors.OKCYAN}Input:{Colors.ENDC} {step_input}")
                        
                        step_output = step.get('output', 'None')
                        if len(str(step_output)) > 200:
                            step_output = str(step_output)[:200] + "..."
                        print(f"  {Colors.OKCYAN}Output:{Colors.ENDC} {step_output}")
                
                # Extract any structured event data from the response
                if verbose:
                    print_section("📊 EXTRACTED EVENT DATA", color=Colors.OKCYAN)
                    # Try to extract structured data from agent output
                    extracted_data = extract_event_data_from_output(agent_output)
                    if extracted_data:
                        for key, value in extracted_data.items():
                            if value:
                                print(f"  {Colors.OKCYAN}{key.title()}:{Colors.ENDC} {value}")
                    else:
                        print("  No structured event data extracted")
                
            else:
                print_section("❌ AGENT EXECUTION FAILED", color=Colors.FAIL)
                error_msg = result.get("error", "Unknown error occurred")
                print(f"Error: {error_msg}")
                
                # Provide helpful troubleshooting suggestions
                if "api" in error_msg.lower():
                    print(f"\n{Colors.WARNING}💡 Troubleshooting:{Colors.ENDC}")
                    print("  - Check your ANTHROPIC_API_KEY in .env file")
                    print("  - Ensure you have sufficient API credits")
                elif "notion" in error_msg.lower():
                    print(f"\n{Colors.WARNING}💡 Troubleshooting:{Colors.ENDC}")
                    print("  - Check your NOTION_TOKEN in .env file")
                    print("  - Verify NOTION_DATABASE_ID is correct")
                    print("  - Ensure the integration has proper permissions")
        
        # Prepare return data
        test_result = {
            "success": result.get("success", False),
            "input": raw_input,
            "source": source,
            "input_type": input_type,
            "agent_output": result.get("agent_output", ""),
            "error": result.get("error") if not result.get("success") else None,
            "reasoning_steps": result.get("reasoning_steps", []) if verbose else None,
            "timestamp": result.get("timestamp"),
            "processing_time": result.get("processing_time")
        }
        
        if json_output:
            print(json.dumps(test_result, indent=2, default=str))
        
        return test_result
        
    except Exception as e:
        error_msg = f"Test execution failed: {str(e)}"
        if not json_output:
            print_section("💥 UNEXPECTED ERROR", error_msg, Colors.FAIL)
            print(f"\n{Colors.WARNING}💡 This might indicate:{Colors.ENDC}")
            print("  - Missing dependencies (run: pip install -r requirements.txt)")
            print("  - Import path issues")
            print("  - Environment configuration problems")
        
        result = {"success": False, "error": error_msg, "input": raw_input, "source": source}
        if json_output:
            print(json.dumps(result, indent=2))
        
        return result


def extract_event_data_from_output(agent_output: str) -> Dict[str, str]:
    """Extract structured event data from agent output text."""
    extracted = {}
    
    # Common patterns for event data
    patterns = {
        "title": [
            r"title[:\s]+([^\n]+)",
            r"event[:\s]+([^\n]+)",
            r"name[:\s]+([^\n]+)"
        ],
        "date": [
            r"date[:\s]+([^\n]+)",
            r"when[:\s]+([^\n]+)",
            r"time[:\s]+([^\n]+)"
        ],
        "location": [
            r"location[:\s]+([^\n]+)",
            r"where[:\s]+([^\n]+)",
            r"venue[:\s]+([^\n]+)"
        ]
    }
    
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, agent_output, re.IGNORECASE)
            if match:
                extracted[field] = match.group(1).strip()
                break
    
    return extracted


def interactive_mode(verbose: bool = False):
    """
    Interactive mode for testing multiple inputs with the agent.
    
    Args:
        verbose: Whether to show detailed output
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}🤖 INTERACTIVE AGENT TESTING{Colors.ENDC}")
    print("Enter content to test (URLs, text descriptions, events) or 'quit' to exit")
    print(f"\n{Colors.OKCYAN}Available Commands:{Colors.ENDC}")
    print("  'verbose on/off'    - Toggle detailed output")
    print("  'source <name>'     - Set input source")
    print("  'type <type>'       - Pre-set input type")
    print("  'type reset'        - Clear input type")
    print("  'env'               - Show environment status")
    print("  'help'              - Show this help")
    print("  'quit' or 'exit'    - Exit interactive mode")
    print("-" * 60)
    
    current_source = "interactive"
    current_type = None
    
    while True:
        try:
            # Show current settings
            settings = f"Source: {current_source}"
            if current_type:
                settings += f", Type: {current_type}"
            if verbose:
                settings += ", Verbose: ON"
            
            user_input = input(f"\n{Colors.BOLD}[{settings}] Enter input: {Colors.ENDC}").strip()
            
            # Handle exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
                break
            
            # Handle commands
            if user_input.lower() == 'verbose on':
                verbose = True
                print(f"{Colors.OKGREEN}✓ Verbose mode enabled{Colors.ENDC}")
                continue
            elif user_input.lower() == 'verbose off':
                verbose = False
                print(f"{Colors.OKGREEN}✓ Verbose mode disabled{Colors.ENDC}")
                continue
            elif user_input.lower().startswith('source '):
                current_source = user_input[7:].strip()
                print(f"{Colors.OKGREEN}✓ Source set to: {current_source}{Colors.ENDC}")
                continue
            elif user_input.lower().startswith('type '):
                if user_input.lower() == 'type reset':
                    current_type = None
                    print(f"{Colors.OKGREEN}✓ Input type reset{Colors.ENDC}")
                else:
                    current_type = user_input[5:].strip()
                    print(f"{Colors.OKGREEN}✓ Input type set to: {current_type}{Colors.ENDC}")
                continue
            elif user_input.lower() == 'env':
                env_status = check_environment()
                print_section("🔧 ENVIRONMENT STATUS", env_status, Colors.OKCYAN)
                continue
            elif user_input.lower() == 'help':
                print(f"\n{Colors.OKCYAN}Available Commands:{Colors.ENDC}")
                print("  'verbose on/off'    - Toggle detailed output")
                print("  'source <name>'     - Set input source")
                print("  'type <type>'       - Pre-set input type")
                print("  'type reset'        - Clear input type")
                print("  'env'               - Show environment status")
                print("  'help'              - Show this help")
                print("  'quit' or 'exit'    - Exit interactive mode")
                continue
            
            if not user_input:
                continue
            
            # Test the input with current settings
            test_agent_flow(
                raw_input=user_input,
                source=current_source,
                input_type=current_type,
                verbose=verbose
            )
            
        except KeyboardInterrupt:
            print(f"\n{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
            break
        except Exception as e:
            print(f"{Colors.FAIL}💥 Error: {e}{Colors.ENDC}")


def validate_input(user_input: str) -> str:
    """
    Validate and normalize input.
    
    Args:
        user_input: User input to validate
        
    Returns:
        Normalized input
        
    Raises:
        ValueError: If input is invalid
    """
    if not user_input or not user_input.strip():
        raise ValueError("Input cannot be empty")
    
    return user_input.strip()


def main():
    """Main CLI interface for agent flow testing."""
    parser = argparse.ArgumentParser(
        description="Test harness for ReAct agent-based event processing in SoBored",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_url_parse.py "https://eventbrite.com/some-event"
  python test_url_parse.py "Concert tonight at 8pm at Central Park"
  python test_url_parse.py "Meeting tomorrow 2pm" --verbose
  python test_url_parse.py --interactive
  python test_url_parse.py "Workshop next Friday" --json --source email

Environment Requirements:
  ANTHROPIC_API_KEY     - Required for Claude API access
  NOTION_TOKEN          - Optional for Notion integration
  NOTION_DATABASE_ID    - Optional for Notion integration

Note: The system will work without Notion credentials but won't save events.
        """
    )
    
    parser.add_argument(
        'input', 
        nargs='?', 
        help='Content to process: URL, text description, event details, etc.'
    )
    parser.add_argument(
        '--source', '-s',
        default='test_harness',
        help='Source of the input (default: test_harness)'
    )
    parser.add_argument(
        '--type', '-t',
        help='Pre-classify input type (url, text, image, etc.)'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode for testing multiple inputs'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output including reasoning steps and environment info'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results as JSON (useful for scripting)'
    )
    parser.add_argument(
        '--check-env',
        action='store_true',
        help='Check environment setup and exit'
    )
    
    args = parser.parse_args()
    
    # Handle environment check
    if args.check_env:
        env_status = check_environment()
        print_section("🔧 ENVIRONMENT STATUS", color=Colors.HEADER)
        
        print(f"\n{Colors.BOLD}Environment Variables:{Colors.ENDC}")
        for var, status in env_status["environment_variables"].items():
            color = Colors.OKGREEN if "✓" in status else Colors.FAIL
            print(f"  {color}{status}{Colors.ENDC} {var}")
        
        print(f"\n{Colors.BOLD}Dependencies:{Colors.ENDC}")
        for dep, status in env_status["dependencies"].items():
            color = Colors.OKGREEN if "✓" in status else Colors.WARNING
            print(f"  {color}{status}{Colors.ENDC} {dep}")
        
        print(f"\n{Colors.BOLD}Agent System:{Colors.ENDC}")
        agent_color = Colors.OKGREEN if "✓" in env_status["agent_system"] else Colors.FAIL
        print(f"  {agent_color}{env_status['agent_system']}{Colors.ENDC}")
        
        # Check if core requirements are met
        anthropic_key = env_status["environment_variables"].get("ANTHROPIC_API_KEY")
        agent_system = env_status["agent_system"]
        
        if "✓" in anthropic_key and "✓" in agent_system:
            print(f"\n{Colors.OKGREEN}✅ Core requirements met - ready for testing!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.FAIL}❌ Core requirements not met{Colors.ENDC}")
            if "✗" in anthropic_key:
                print("  - Add ANTHROPIC_API_KEY to your .env file")
            if "✗" in agent_system:
                print("  - Fix agent system import issues")
            sys.exit(1)
    
    # Check for required environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print(f"{Colors.FAIL}💥 ANTHROPIC_API_KEY not found in environment{Colors.ENDC}")
        print("Add your Claude API key to the .env file:")
        print("ANTHROPIC_API_KEY=your-key-here")
        print(f"\nUse {Colors.BOLD}--check-env{Colors.ENDC} to see full environment status")
        sys.exit(1)
    
    # Handle interactive mode
    if args.interactive:
        interactive_mode(verbose=args.verbose)
    elif args.input:
        try:
            validated_input = validate_input(args.input)
            test_agent_flow(
                raw_input=validated_input,
                source=args.source,
                input_type=args.type,
                verbose=args.verbose,
                json_output=args.json
            )
        except ValueError as e:
            print(f"{Colors.FAIL}💥 {e}{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"{Colors.FAIL}💥 Please provide input or use --interactive mode{Colors.ENDC}")
        print(f"Use {Colors.BOLD}--help{Colors.ENDC} for usage information")
        print(f"Use {Colors.BOLD}--check-env{Colors.ENDC} to check your environment setup")
        sys.exit(1)


if __name__ == '__main__':
    main()