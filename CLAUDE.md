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

# Test the smart pipeline directly
python test_smart_pipeline.py  # Test new optimized pipeline

# Test the ReAct agent pipeline directly  
python test_url_parse.py "https://example.com/event"
python test_url_parse.py "Concert tonight at 8pm"

# Compare both systems
python run_comparison_experiment.py  # Compare performance
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
  ANTHROPIC_API_KEY=your-claude-api-key
  LANGSMITH_API_KEY=your-langsmith-api-key
  USE_SMART_PIPELINE=false  # Set to 'true' to enable optimized pipeline
  ```
- Set Telegram webhook: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://abc123.ngrok.io/telegram/webhook`
- Set up Notion integration and database using `python test_run_graph.py`

## Development Practices

### Package Management
- Always add to `requirements.txt` when adding new packages
- Ensure all team members have consistent dependencies

## Architecture Overview

This is a smart event aggregator with **dual processing modes**:

### Smart Pipeline (Optimized - Default when USE_SMART_PIPELINE=true)
- **3-tier classification**: Regex → ML → LLM (only for complex cases)
- **Specialized processors**: Direct URL/text processing without agent overhead
- **Performance**: ~5x faster than ReAct agent (18s → <5s)
- **Efficiency**: 95%+ cases handled without LLM classification calls

### ReAct Agent (Legacy - Fallback when USE_SMART_PIPELINE=false)
- **LangChain ReAct Agents** with **LangGraph tools** for content processing
- Full reasoning cycles for all operations
- Comprehensive but slower processing
- Fallback for complex edge cases

Both modes use **Telegram Bot** as the primary interface and integrate with **LangSmith** for evaluation and feedback collection.

## Workflow Practices
- Always update readme.md and claude.md when making changes that impact those files' contents