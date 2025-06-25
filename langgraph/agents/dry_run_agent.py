"""
Dry-run event processing ReAct agent for testing URL parsing without Notion commits.
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic

from .tools import classify_input, fetch_url_content, parse_url_content
from .tools.save_notion_tool import save_to_notion
from ..observability.langsmith_config import create_langsmith_config
from ..observability.structured_logging import ReActAgentLogger


class DryRunEventProcessingAgent:
    """
    Dry-run ReAct agent for testing event processing without committing to Notion.
    
    This agent uses the same tools as the main agent, but ensures dry-run mode is enabled
    by setting DRY_RUN=true in the environment. The unified save_to_notion tool will
    automatically perform mock saves without making actual API calls.
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """
        Initialize the dry-run event processing agent.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use for reasoning
        """
        import os
        
        # Ensure dry-run mode is enabled for this agent
        os.environ["DRY_RUN"] = "true"
        print("[DRY-RUN AGENT] Initializing dry-run agent with DRY_RUN=true")
        self.llm = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0.1
        )
        
        # Initialize observability
        self.logger = ReActAgentLogger("dry_run_event_processor")
        self.langsmith_config = create_langsmith_config()
        
        # Available tools for the agent (using unified save tool with dry-run mode)
        self.tools = [
            classify_input,
            fetch_url_content,
            parse_url_content,
            save_to_notion  # Now uses unified tool that respects DRY_RUN environment variable
        ]
        
        print(f"[DRY-RUN AGENT] Available tools: {[tool.name for tool in self.tools]}")
        
        # Create the ReAct agent and executor
        self.agent_executor = self._create_agent_executor()
    
    def _create_agent_executor(self):
        """Create the ReAct agent executor with tools and prompt."""
        
        # Use the standard ReAct prompt from LangChain hub
        try:
            prompt = hub.pull("hwchase17/react")
        except:
            # Fallback to a simple working ReAct prompt
            prompt_template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
            prompt = PromptTemplate.from_template(prompt_template)
        
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,  # Enable verbose to see agent reasoning
            return_intermediate_steps=True,
            max_iterations=8,  # Reduced to fail faster on loops
            max_execution_time=30,  # 30 seconds timeout
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    def process_event(
        self, 
        raw_input: str, 
        source: str = "unknown",
        input_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an event input through the dry-run ReAct agent.
        
        Args:
            raw_input: Raw input content to process
            source: Source of the input (test_harness, etc.)
            input_type: Pre-classified input type (optional)
            user_id: User ID from Telegram or other source (optional)
            
        Returns:
            Dict containing processing results and agent reasoning (with dry-run indicators)
        """
        import time
        
        start_time = time.time()
        
        try:
            # Prepare the input for the agent
            user_info = f"\nUser ID: {user_id}" if user_id else ""
            agent_input = {
                "input": f"""Process this event input in DRY-RUN mode (no actual saves to Notion):

Raw Input: {raw_input}
Source: {source}
Pre-classified Type: {input_type or 'Not specified'}{user_info}

Please classify, process, and show what event information would be saved to Notion. The save_to_notion tool is configured for dry-run mode and will automatically perform mock saves without making actual API calls. Include the user_id in the event data when showing what would be saved."""
            }
            
            # Run the agent executor with LangSmith configuration
            config = self.langsmith_config.copy()
            if config:
                print("[DRY-RUN AGENT] Running with LangSmith tracing enabled")
            
            result = self.agent_executor.invoke(agent_input, config=config)
            
            # Log successful execution
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_agent_invocation_end(
                user_id=user_id,
                source=source,
                success=True,
                duration_ms=duration_ms
            )
            
            return {
                "success": True,
                "raw_input": raw_input,
                "source": source,
                "agent_output": result.get("output", ""),
                "reasoning_steps": self._extract_reasoning_steps(result),
                "dry_run": True,  # Mark this as a dry-run result
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            # Log error execution
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_agent_invocation_end(
                user_id=user_id,
                source=source,
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )
            
            return {
                "success": False,
                "error": str(e),
                "raw_input": raw_input,
                "source": source,
                "dry_run": True,
                "duration_ms": duration_ms
            }
    
    def _extract_reasoning_steps(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract reasoning steps from agent output for debugging.
        
        Args:
            result: Agent execution result
            
        Returns:
            List of reasoning steps
        """
        steps = []
        
        try:
            # Parse the agent's intermediate steps if available
            if "intermediate_steps" in result and result["intermediate_steps"]:
                for step in result["intermediate_steps"]:
                    if hasattr(step, "tool") and hasattr(step, "tool_input"):
                        steps.append({
                            "action": step.tool,
                            "input": str(step.tool_input),
                            "output": str(step.observation) if hasattr(step, "observation") else ""
                        })
            
            # Alternative: try to extract from agent scratchpad or other fields
            elif "agent_scratchpad" in result:
                # Basic parsing of agent scratchpad text
                scratchpad = result.get("agent_scratchpad", "")
                if scratchpad:
                    steps.append({
                        "action": "agent_reasoning",
                        "input": "internal_reasoning",
                        "output": scratchpad[:500] + "..." if len(scratchpad) > 500 else scratchpad
                    })
        except Exception as e:
            # If reasoning step extraction fails, just log it and continue
            steps.append({
                "action": "extraction_error",
                "input": "reasoning_steps",
                "output": f"Failed to extract reasoning steps: {str(e)}"
            })
        
        return steps


def create_dry_run_event_agent(api_key: str, model: str = "claude-3-haiku-20240307") -> DryRunEventProcessingAgent:
    """
    Factory function to create a dry-run event processing agent.
    
    Args:
        api_key: Anthropic API key
        model: Claude model to use
        
    Returns:
        Configured DryRunEventProcessingAgent instance
    """
    return DryRunEventProcessingAgent(api_key, model)