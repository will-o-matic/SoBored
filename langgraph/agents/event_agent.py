"""
Event processing ReAct agent for the SoBored event aggregator.
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic

from .tools import classify_input, fetch_url_content, parse_url_content, save_to_notion
from ..mcp import initialize_mcp_for_agent


class EventProcessingAgent:
    """
    ReAct agent for processing events from various input sources.
    
    This agent uses LangChain's ReAct pattern to:
    1. Classify input content (text, URL, image, etc.)
    2. Fetch and parse content as needed
    3. Save structured event data to Notion
    4. Respond with processing results
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", use_mcp: bool = False):
        """
        Initialize the event processing agent.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use for reasoning
            use_mcp: Whether to attempt MCP integration
        """
        self.llm = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0.1
        )
        
        # Available tools for the agent
        self.tools = [
            classify_input,
            fetch_url_content,
            parse_url_content,
            save_to_notion
        ]
        
        # Optionally add MCP tools
        self.mcp_client = None
        if use_mcp:
            try:
                import asyncio
                self.mcp_client = asyncio.run(initialize_mcp_for_agent())
                if self.mcp_client.is_available():
                    mcp_tools = self.mcp_client.get_tools()
                    self.tools.extend(mcp_tools)
                    print(f"Added {len(mcp_tools)} MCP tools to agent")
            except Exception as e:
                print(f"MCP integration failed: {e}")
        
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
        Process an event input through the ReAct agent.
        
        Args:
            raw_input: Raw input content to process
            source: Source of the input (telegram, web, etc.)
            input_type: Pre-classified input type (optional)
            user_id: User ID from Telegram or other source (optional)
            
        Returns:
            Dict containing processing results and agent reasoning
        """
        try:
            # Prepare the input for the agent
            user_info = f"\nUser ID: {user_id}" if user_id else ""
            agent_input = {
                "input": f"Process this event input:\n\nRaw Input: {raw_input}\nSource: {source}\nPre-classified Type: {input_type or 'Not specified'}{user_info}\n\nPlease classify, process, and save this event information to Notion if it contains event details. Include the user_id in the event data when saving to Notion."
            }
            
            # Run the agent executor
            result = self.agent_executor.invoke(agent_input)
            
            return {
                "success": True,
                "raw_input": raw_input,
                "source": source,
                "agent_output": result.get("output", ""),
                "reasoning_steps": self._extract_reasoning_steps(result)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_input": raw_input,
                "source": source
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


def create_event_agent(api_key: str, model: str = "claude-3-haiku-20240307", use_mcp: bool = False) -> EventProcessingAgent:
    """
    Factory function to create an event processing agent.
    
    Args:
        api_key: Anthropic API key
        model: Claude model to use
        use_mcp: Whether to attempt MCP integration
        
    Returns:
        Configured EventProcessingAgent instance
    """
    return EventProcessingAgent(api_key, model, use_mcp)