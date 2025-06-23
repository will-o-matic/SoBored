# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Use Context7 for up-to-date documentation.

## Project Location
- **Recommended**: WSL filesystem at `~/SoBored` for Windows users
- **Legacy**: Windows filesystem at `/mnt/c/users/will/documents/codingprojects/SoBored` (slower, permission issues)

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server (port 8000)
uvicorn telegram-bot.main:app --reload --port 8000

# In a separate terminal, expose with ngrok
ngrok http 8000

# Test the ReAct agent pipeline directly  
python test_url_parse.py "https://example.com/event"
python test_url_parse.py "Concert tonight at 8pm"
```

### Development Utilities
```bash
# Notion API utilities for development and debugging
python -m utils.notion_dev_utils validate-token      # Check token and permissions
python -m utils.notion_dev_utils list-databases      # List accessible databases
python -m utils.notion_dev_utils database-info <id>  # Get database details
python -m utils.notion_dev_utils create-database     # Create new database
python -m utils.notion_dev_utils query-pages <id>    # List pages in database
python -m utils.notion_dev_utils export-database <id> --format csv  # Export data
python -m utils.notion_dev_utils clean-database <id> --dry-run      # Test cleanup
```

### Environment Setup
- Create `.env` file with required tokens:
  ```
  TELEGRAM_BOT_TOKEN=your-token-here
  NOTION_TOKEN=your-notion-integration-token
  NOTION_DATABASE_ID=your-notion-database-id
  ```
- Set Telegram webhook: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://abc123.ngrok.io/telegram/webhook`
- Set up Notion integration and database using `python test_run_graph.py`

## Architecture Overview

This is a smart event aggregator using **LangChain ReAct Agents** with **LangGraph tools** for content processing and **Telegram Bot** as the primary interface. The system has been refactored from custom StateGraph to proper ReAct agent pattern with MCP integration.

### Core Components

**ReAct Agent System** (`langgraph/main_agent.py`):
- Uses `create_react_agent()` with LangChain tools following ReAct reasoning pattern
- Flow: Input → Agent reasoning → Tool invocation → Save to Notion → Respond
- Supports MCP (Model Context Protocol) integration for enhanced tool capabilities

**Agent Tools** (`langgraph/agents/tools/`):
- `classify_input`: @tool decorated function for input classification (text, URL, image, etc.)
- `fetch_url_content`: @tool for webpage content fetching with MCP/requests fallback
- `parse_url_content`: @tool for Claude-powered event extraction from webpage content
- `save_to_notion`: @tool for structured Notion database integration

**State Management** (Legacy `utils/state.py`):
- `EventState` still used for backward compatibility with Telegram integration
- Core fields: `input_type`, `raw_input`, `source`, `event_*` parsed fields
- Agent system handles state internally but provides compatibility layer

**Telegram Integration** (`telegram-bot/main.py`):
- FastAPI app with `/telegram/webhook` endpoint
- Converts Telegram message format and calls `process_event_input()`
- Uses ReAct agent via `langgraph.main_agent.process_event_input()`
- Maintains backward compatibility with EventState format

**MCP Integration** (`langgraph/mcp/`):
- `MCPClientWrapper` for integrating Model Context Protocol tools
- Automatic detection and integration of available MCP servers
- Fallback to requests/BeautifulSoup when MCP unavailable
- Supports web fetch, filesystem, and other MCP tool capabilities

**Notion Integration** (`utils/notion_client.py`):
- `NotionClientWrapper` class handles all Notion API interactions
- Database creation, page creation, querying, and error handling
- `create_events_database_schema()` defines structured database schema
- Comprehensive error handling for permissions, rate limits, and connectivity

### Data Flow (New ReAct Agent Architecture)
1. Input received (Telegram webhook, test harness, etc.) → `process_event_input()`
2. ReAct agent created with available tools (classification, fetch, parse, save)
3. Agent uses reasoning loop: Thought → Action → Observation → repeat
4. Agent invokes tools as needed: classify → fetch (URLs) → parse → save to Notion
5. Agent provides final reasoning and response with processing results
6. Response returned to caller (Telegram, test harness, etc.)

### Current Architecture (Implemented)
**ReAct Agent System**:
- Input → Agent Reasoning → Tool Selection → Action Execution → Notion Save → Response
- Support for text, URLs, and image inputs (image processing via Claude vision)
- MCP integration for enhanced web fetching and tool capabilities
- Comprehensive error handling and fallback mechanisms

**Legacy StateGraph Support**:
- Original node-based system available via `--legacy` flag in test harness
- Backward compatibility maintained for existing integrations
- Gradual migration path for production systems

### Future Architecture Expansion
The ReAct agent system enables easy expansion:
- **Enhanced Tools**: Add validation, deduplication, enrichment tools to agent toolkit
- **Multiple Agents**: Specialized agents for different input types or processing stages  
- **MCP Ecosystem**: Leverage growing MCP tool ecosystem for web scraping, OCR, etc.
- **Multi-modal**: Better image processing, audio transcription, document analysis
- **Workflow Orchestration**: LangGraph for complex multi-agent workflows

## Development Patterns

### ReAct Agent Tool Development  
- **Tool Structure**: Use `@tool` decorator with type hints and comprehensive docstrings
- **Tool Location**: Place tools in `langgraph/agents/tools/` directory with `_tool.py` suffix
- **Error Handling**: Tools should return structured error information rather than raising exceptions
- **Import Pattern**: Import tools in agent as `from .tools import tool_name`

### Dry-Run Development Patterns
- **Dry-Run Tools**: Create non-destructive versions of tools that show intended actions
- **Agent Variants**: Separate dry-run agents that use mock tools instead of live APIs
- **Testing Workflow**: Develop with dry-run mode, validate behavior, then switch to production
- **Data Validation**: Use dry-run to verify data extraction accuracy before committing
- **Safe Development**: Test new parsing logic without polluting production databases

### Legacy Node Development (Deprecated)
- **Legacy Support**: Original node-based system in `langgraph/nodes/` still available
- **Migration Path**: Convert nodes to tools using `@tool` decorator pattern
- **Backward Compatibility**: Use `--legacy` flag in test harness for old behavior

### Testing Strategy
**Agent Testing** (recommended approach):
- Use `python test_url_parse.py` for comprehensive agent flow testing
- Test different input types: URLs, text descriptions, structured events
- Interactive mode: `python test_url_parse.py --interactive`
- **Dry-run mode**: `python test_url_parse.py --dry-run` for safe testing without Notion commits

**Dry-Run Testing Patterns**:
- **Development**: Use `--dry-run` to test event parsing logic without side effects
- **Debugging**: See exactly what would be saved to Notion before committing
- **Interactive Development**: `python test_url_parse.py --interactive --dry-run` for rapid iteration
- **CI/CD**: Incorporate dry-run tests in automated testing pipelines
- **Validation**: Verify parsing accuracy before switching to production mode

**Tool Testing** (for development):
- Test individual tools in isolation using LangChain tool testing patterns
- Use `test_agent_flow()` function for end-to-end agent workflows
- Verify tool invocation patterns and error handling
- Test both regular and dry-run tool variants

**Integration Testing**:
- **Dry-run Integration**: Test full pipeline without external side effects
- **Production Integration**: Test end-to-end flow: Input → Agent → Tools → Notion → Response
- **Telegram Integration**: Test with actual Telegram message payloads via webhook
- **MCP Integration**: Verify MCP integration and fallback mechanisms

### Code Organization
**Agent Architecture**:
- **Agent Classes**: Main agents in `langgraph/agents/` (e.g., `event_agent.py`, `dry_run_agent.py`)
- **Tool Functions**: Individual tools in `langgraph/agents/tools/`
- **Dry-Run Tools**: Non-destructive versions (e.g., `dry_run_save_notion_tool.py`)
- **MCP Integration**: MCP client and configuration in `langgraph/mcp/`
- **Main Entry Point**: `langgraph/main_agent.py` for unified agent access

**Legacy Components** (maintained for compatibility):
- **State Objects**: `utils/state.py` for EventState and Telegram integration
- **Node Functions**: `langgraph/nodes/` for original StateGraph approach
- **Graph Assembly**: `langgraph/main_graph.py` for legacy graph construction

**External Integrations**:
- **Telegram Bot**: `telegram-bot/` directory
- **Notion Integration**: `utils/notion_client.py` and tools
- **Environment**: All secrets in `.env`, never commit tokens

### Error Handling Patterns
**Agent-Level Errors**:
- ReAct agents handle tool failures gracefully with reasoning
- Agents provide detailed error context and recovery suggestions
- MCP integration includes automatic fallback to requests/BeautifulSoup

**Tool-Level Errors**:
- Tools return structured error dictionaries rather than raising exceptions
- Include specific error types for different failure modes (API, network, validation)
- Provide actionable error messages for debugging and user feedback

**System-Level Errors**:
- Environment validation at startup (API keys, database connections)
- Graceful degradation when optional services (MCP, Notion) unavailable
- Comprehensive logging for debugging and monitoring