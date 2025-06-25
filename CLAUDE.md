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

# Test with dry-run mode (no actual Notion saves)
DRY_RUN=true python test_smart_pipeline.py  # Test without API calls
DRY_RUN=true python test_url_parse.py "https://example.com/event"
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
  DRY_RUN=false  # Set to 'true' to enable dry-run mode (no actual Notion API calls)
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

## Recent Updates

### Multi-Date Event Support (v1.1.0)
- **Enhanced Database Schema**: Added dedicated fields for series linking (Series ID, Session Number, Total Sessions, Recurrence)
- **Smart Pipeline Optimization**: Implemented multi-instance event handling with proper series metadata
- **Evaluation Framework**: Comprehensive LangSmith evaluation system for multi-date event testing
- **Date Parsing Fix**: Added current year context to LLM prompts for accurate date interpretation

### Evaluation & Testing
```bash
# Run multi-date evaluation framework
python setup_multi_date_evaluation.py

# Test date parsing fix specifically  
python test_date_parsing_fix.py

# Update Notion database schema for multi-date support
python update_notion_schema.py [--dry-run] [--database-id ID]
```

### Date Context Enhancement
- **Issue Fixed**: Relative dates like "June 25th" now correctly parse as current year (2025) instead of defaulting to past years
- **Text Processor**: Updated LLM prompts to include current date context
- **URL Processor**: Already had proper date context handling
- **Validation**: All date parsing tests now pass with correct year interpretation

### Text Processor Multi-Date Enhancement (v1.2.0)
- **Issue Fixed**: Multi-date text events like "June 24, June 26, and June 28 at 2PM" now extract all dates correctly
- **Prompt Improvements**: Enhanced LLM instructions for comma-separated multi-date extraction
- **Pattern Recognition**: Distinguishes explicit date lists from recurring patterns
- **Performance**: Multi-date text events now create proper series with session counts and linking
- **Validation**: LangSmith trace b51775d9-9966-485d-9940-856c92f9c441 now processes correctly

## Workflow Practices
- Always update readme.md and claude.md when making changes that impact those files' contents