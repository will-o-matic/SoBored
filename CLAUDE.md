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

## Development Practices

### Package Management
- Always add to `requirements.txt` when adding new packages
- Ensure all team members have consistent dependencies

## Architecture Overview

This is a smart event aggregator using **LangChain ReAct Agents** with **LangGraph tools** for content processing and **Telegram Bot** as the primary interface. The system has been refactored from custom StateGraph to proper ReAct agent pattern with MCP integration.

## Workflow Practices
- Always update readme.md and claude.md when making changes that impact those files' contents