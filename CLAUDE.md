# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.  Use Context7 for up-to-date documentation.

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server (port 8000)
uvicorn telegram-bot.main:app --reload --port 8000

# In a separate terminal, expose with ngrok
ngrok http 8000

# Test the LangGraph pipeline directly
python test_run_graph.py
```

### Environment Setup
- Create `.env` file with `TELEGRAM_BOT_TOKEN=your-token-here`
- Set Telegram webhook: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://abc123.ngrok.io/telegram/webhook`

## Architecture Overview

This is a smart event aggregator using **LangGraph** for content classification and **Telegram Bot** as the primary interface.

### Core Components

**LangGraph Pipeline** (`langgraph/main_graph.py`):
- Uses `StateGraph(EventState)` with a single "classifier" node
- Entry point and finish point both at classifier (MVP setup)
- Compiles to `app` that can be invoked with EventState

**State Management** (`utils/state.py`):
- `EventState` is a Pydantic model with `input_type`, `raw_input`, and `source` fields
- Shared state object flows through the entire LangGraph pipeline

**Classification Logic** (`langgraph/nodes/classifier_node.py`):
- `classify_input()` function takes EventState and returns updated EventState
- Detects: image (via pre-set input_type), URL (regex), text, or unknown
- Simple regex-based URL detection: `r'https?://\S+'`

**Telegram Integration** (`telegram-bot/main.py`):
- FastAPI app with `/telegram/webhook` endpoint
- Converts Telegram message format to EventState
- Invokes LangGraph app and responds with classification result
- Uses `python-telegram-bot` library for sending responses

### Data Flow
1. Telegram webhook receives message → FastAPI endpoint
2. Message converted to EventState (raw_input, input_type, source)
3. EventState passed to LangGraph app.invoke()
4. Classifier node processes and updates input_type
5. Result sent back to Telegram chat

### Future Architecture (from README)
The system is designed to expand into a full event processing pipeline:
- Input → Classify → Parse → Validate → Deduplicate → Enrich → Save to Notion → Respond
- Additional input sources: web scraping, email, Instagram
- Notion database storage with fields: Title, Date/Time, Location, Description, etc.

## Development Patterns

### LangGraph Node Development
- **Node Structure**: Each node is a function that takes `EventState` and returns `EventState`
- **Node Location**: Place nodes in `langgraph/nodes/` directory with `_node.py` suffix
- **State Updates**: Always return the modified state object, don't mutate in place
- **Import Pattern**: Import nodes in `main_graph.py` as `from langgraph.nodes import node_name`

### Testing Strategy
**Manual Testing** (current approach):
- Use `test_run_graph.py` to test the LangGraph pipeline directly
- Test different input types: text, URLs, and images
- Verify state transformations through the pipeline

**Unit Testing** (recommended for expansion):
- Test individual nodes in isolation: `test_classifier_node.py`
- Test state object creation and validation: `test_event_state.py`
- Test FastAPI endpoints separately from LangGraph logic
- Use pytest framework when adding formal tests

**Integration Testing**:
- Test end-to-end flow: Telegram webhook → LangGraph → response
- Test with actual Telegram message payloads
- Verify webhook setup and ngrok integration

### Code Organization
- **State Objects**: Keep all shared state in `utils/state.py`
- **Node Functions**: One file per node type in `langgraph/nodes/`
- **Graph Assembly**: Main graph construction in `langgraph/main_graph.py`
- **External Integrations**: Separate directories (e.g., `telegram-bot/`, future `notion/`)
- **Environment**: All secrets in `.env`, never commit tokens

### Error Handling Patterns
- **Node Failures**: Nodes should handle their own errors and update state accordingly
- **API Failures**: Telegram/external API calls should have retry logic and fallbacks
- **Invalid Input**: Classifier should handle unknown/malformed input gracefully
- **State Validation**: Use Pydantic validation in EventState for type safety