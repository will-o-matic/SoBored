# SoBored App

A smart event aggregator and assistant that helps surface interesting things to do in your city. It pulls event data from multiple input channels (flyers, URLs, text, etc.), extracts structured event info, and saves it to a Notion database for exploration and querying.

---

## 🚀 Getting Started (Telegram Bot + FastAPI + LangGraph + ngrok)

This project sets up a Telegram bot that receives user messages, classifies the content (text, image, or URL), and replies with the classification. It uses:

- **FastAPI** to handle Telegram webhooks
- **LangGraph** to classify content type
- **ngrok** to expose your local server during development
- **python-dotenv** to securely manage secrets

---

### 🔧 Prerequisites

- Python 3.9+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Notion integration and database (see Notion Setup below)
- `ngrok` installed (`brew install ngrok`, `choco install ngrok`, or download from https://ngrok.com)

### 🪟 VS Code + WSL Setup (Windows Users)

For the best development experience on Windows, use VS Code with the Remote-WSL extension to work directly in the WSL filesystem.

#### Initial Setup
1. **Install Prerequisites:**
   - [VS Code](https://code.visualstudio.com/)
   - [Remote - WSL extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl)
   - [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install)

2. **Clone Project to WSL Filesystem:**
   ```bash
   # In WSL terminal, clone to your home directory (works best for WSL and Claude Code)
   cd ~
   git clone https://github.com/your-username/SoBored.git
   cd SoBored
   ```

3. **Open in VS Code:**
   ```bash
   # From WSL terminal in the project directory
   code .
   ```
   This will open VS Code in Remote-WSL mode with the project loaded.

#### Python Environment Setup
```bash
# Create virtual environment in WSL filesystem
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Install ngrok in WSL
```bash
# Install ngrok directly in WSL
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Or download manually:
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin
```

#### VS Code Remote-WSL Benefits
- **Seamless file editing**: Edit files directly in WSL filesystem
- **Integrated terminal**: VS Code terminal runs in WSL context
- **Extension support**: Install Python extensions that work with WSL
- **Git integration**: Works natively with WSL git
- **Debugging**: Full debugging support for Python apps

#### Access from Windows File Explorer
You can still access your WSL project files from Windows at:
```
\\wsl$\Ubuntu\home\yourusername\SoBored
```

#### Claude Code Usage
When using Claude Code CLI:
```bash
# In WSL terminal, navigate to project
cd ~/SoBored
# Claude Code will work seamlessly with files in WSL filesystem
```

**Why This Setup Works Better:**
- Faster file operations (no Windows/WSL filesystem bridge)
- Better permissions handling
- Native Linux tooling performance
- Seamless integration between VS Code and WSL

---

### 📦 Install Dependencies

Create a virtual environment and install required packages:

```bash
pip install -r requirements.txt
```

Create a .env file at the project root with:

```
TELEGRAM_BOT_TOKEN=your-telegram-token-here
NOTION_TOKEN=your-notion-integration-token-here
NOTION_DATABASE_ID=your-notion-database-id-here
```

Make sure .env is listed in .gitignore to avoid committing secrets.

Start the local webhook server on port 8000:

uvicorn telegram-bot.main:app --reload --port 8000

In a separate terminal:

ngrok http 8000

Copy the HTTPS forwarding URL (e.g. https://abc123.ngrok.io).

Set your webhook using your bot token and ngrok URL:

https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://abc123.ngrok.io/telegram/webhook

Replace:

    <YOUR_BOT_TOKEN> with your real token

    https://abc123.ngrok.io with your actual ngrok URL

A successful response will look like:

{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}

### 🗃️ Notion Setup

1. Create a Notion integration at https://www.notion.com/my-integrations
2. Copy the integration token to your `.env` file as `NOTION_TOKEN`
3. Create or select a Notion page where you want your events database
4. Share the page with your integration (Share → Add connections)
5. Run the database setup:
   ```bash
   python test_run_graph.py
   ```
6. Follow the prompts to create your events database
7. Copy the database ID to your `.env` file as `NOTION_DATABASE_ID`

🧪 Test It!

Send your bot a message:

    Text → it should reply “Classified as: text”

    A URL → reply: “Classified as: url”

    An image → reply: “Classified as: image”

You should see FastAPI and ngrok logs updating as requests come in.

## 🛠️ Development Utilities

The project includes a comprehensive utility script for common Notion API tasks during development.

### Notion Development Utilities

Use the `notion_dev_utils.py` script for database management and debugging:

```bash
# Validate your Notion token and permissions
python -m utils.notion_dev_utils validate-token

# List all databases accessible to your integration
python -m utils.notion_dev_utils list-databases

# Get detailed information about a specific database
python -m utils.notion_dev_utils database-info <database_id>

# Create a new database interactively
python -m utils.notion_dev_utils create-database

# Query pages in a database
python -m utils.notion_dev_utils query-pages <database_id> --limit 10

# List pages from a specific database or search all accessible pages
python -m utils.notion_dev_utils list-pages --database-id <database_id> --limit 10
python -m utils.notion_dev_utils list-pages --limit 20  # Search all accessible pages

# Export database contents to JSON or CSV
python -m utils.notion_dev_utils export-database <database_id> --format json
python -m utils.notion_dev_utils export-database <database_id> --format csv

# Clean up database (remove all pages) - useful for testing
python -m utils.notion_dev_utils clean-database <database_id> --dry-run
python -m utils.notion_dev_utils clean-database <database_id>
```

### URL Parse Test Harness

For testing URL parsing flow with optional Notion integration:

```bash
# Test a single URL (with Notion save)
python test_url_parse.py "https://eventbrite.com/some-event"

# DRY-RUN MODE: Test parsing without saving to Notion
python test_url_parse.py "https://eventbrite.com/some-event" --dry-run

# Interactive mode for testing multiple URLs
python test_url_parse.py --interactive

# Interactive mode with dry-run (no Notion commits)
python test_url_parse.py --interactive --dry-run

# Verbose output with full state inspection
python test_url_parse.py "https://example.com" --verbose --dry-run

# JSON output for scripting
python test_url_parse.py "https://example.com" --json
```

#### Test Modes

**Regular Mode**: Full agent pipeline including Notion save
- **classifier**: Detects if input is a URL
- **url_fetcher**: Fetches webpage content 
- **url_parser**: Extracts event details using Claude API
- **save_to_notion**: Creates actual Notion database entry

**Dry-Run Mode** (`--dry-run`): Parse and validate without Notion commits
- Same classification and parsing steps
- Shows what **would** be saved to Notion
- Perfect for testing event extraction logic
- No actual API calls to Notion database

Use dry-run mode when you want to:
- Test URL parsing logic without side effects
- Debug event extraction from webpages
- Validate parsing accuracy before committing data
- Develop and test parsing improvements safely

### Common Development Workflows

**Setting up a new environment:**
1. Run `python -m utils.notion_dev_utils validate-token` to check your token
2. Run `python -m utils.notion_dev_utils create-database` to create your events database
3. Add the database ID to your `.env` file

**Testing URL parsing:**
1. Use `python test_url_parse.py --interactive --dry-run` to safely test multiple URLs
2. Check parsing confidence scores and extracted event details without Notion commits
3. Use `--verbose` to debug parsing issues and see full agent reasoning
4. Switch to regular mode (no `--dry-run`) when ready to save real data

**Debugging Notion issues:**
1. Use `validate-token` to verify authentication
2. Use `list-databases` to see what's accessible
3. Use `database-info` to inspect schema and properties

**Testing and cleanup:**
1. Use `clean-database --dry-run` to see what would be deleted
2. Use `export-database` to backup before cleaning
3. Use `query-pages` or `list-pages` to verify operations

**Page management:**
1. Use `list-pages` to search all accessible pages across workspaces
2. Use `list-pages --database-id <id>` to list pages from a specific database
3. Use `query-pages` for detailed database-specific page queries

---
## Tech Stack

| Layer | Technology |
|-------|------------|
| Chat Interface | Telegram Bot (MVP), Web UI (Future) |
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| Parsing / NLP | [LangChain](https://www.langchain.com/) tools + custom logic |
| Event Storage | Notion database via API (MCP optional later) |
| Deployment | Vercel (API endpoints + front-end) |

---

## MVP Features

- Users can send **text, images, or URLs** to the Telegram bot.
- System parses event info (title, date, location, etc.) from the input.
- Structured event data is saved to a **Notion database**.
- Bot replies with a confirmation (or error handling if info is missing).

---

## Architecture Overview

### Interfaces Layer
- **Telegram Bot**: Receives user messages and sends them to a LangGraph processing pipeline.
- (Future) **Web-based Chat UI** via Next.js + Vercel
- (Optional) **Discord bot**, Email input, or Instagram scraping

### LangGraph Processing Flow

```text
Input → Classify →
  → Image → OCR → Parse → Validate
  → Text → Parse → Validate
  → URL → Scrape → Parse → Validate
→ Deduplicate
→ Enrich (if needed)
→ Save to Notion
→ Respond to user
````

Each step is a LangGraph node (LangChain tools, custom code, or API call). All steps work on a shared `event_state` object that accumulates metadata.

### Notion DB Schema (Implemented)

| Field          | Type         | Description |
| -------------- | ------------ | ----------- |
| Title          | Title        | Event name or generated title |
| Date/Time      | Date         | Event date/time |
| Location       | Rich Text    | Event location/venue |
| Description    | Rich Text    | Event description or raw input |
| Source         | Select       | Input source (telegram, web, email, instagram) |
| URL            | URL          | Link if input was a URL |
| Classification | Select       | Input type (event, url, text, image, unknown) |
| Status         | Select       | Processing status (new, processed, archived) |
| UserId         | Rich Text    | User ID from Telegram or other source |
| Added          | Date         | Timestamp when record was created |

---

## Future Expansion Plan

### Enrichment via LangGraph

* Hydrate missing fields by scraping source URLs or using APIs (e.g., Google Maps for venue resolution).
* Geotag events for map-based UI later.

### Notion Monitoring

* **Pull-based:** Cron job checks for new rows (`hydrated = false`) and enriches them.
* **Push-based:** (When supported) Use Notion webhooks or MCP to trigger enrichment pipelines on update.

### Additional Input Sources

* Web crawling for known venues
* Email newsletter parsing (via forwarding)
* Instagram post parsing (caption + image OCR)

### Front-End Plans

* Build a **Next.js web app** to:

  * Browse and filter events
  * Upload flyers or links
  * Explore events via calendar or map views

---

## Example User Interactions

| Input                                   | Behavior                                               |
| --------------------------------------- | ------------------------------------------------------ |
| Flyer image                             | OCR → parse → save → reply: "Added *Live Jazz at 8pm*" |
| Text: "Art show at Dolores Park on Sat" | NLP → save → reply with confirmation                   |
| URL                                     | Scrape → parse → validate → save → reply with confirmation  |

---

## 📋 Release Notes

### v1.0.0 - Smart Pipeline Performance Revolution (2025-06-24)

🚀 **Major Performance Breakthrough**: Introduced optimized Smart Pipeline architecture alongside existing ReAct agent system.

#### 🏆 **Performance Achievements**
- **9.26x Speed Improvement**: Event processing time reduced from ~18s to <2s
- **95%+ Classification Efficiency**: Instant regex-based classification eliminates LLM calls for obvious cases
- **100% Accuracy Maintained**: Performance gains with no loss in extraction quality

#### 🔧 **New Features**
- **Dual-Mode Architecture**: Smart Pipeline (optimized) + ReAct Agent (fallback)
- **3-Tier Classification System**: Regex → ML → LLM (only for complex cases)
- **Feature Flag Control**: `USE_SMART_PIPELINE=true/false` for gradual rollout
- **LangSmith Integration**: Comprehensive evaluation and feedback collection
- **Performance Monitoring**: Real-time metrics and before/after comparisons

#### 📊 **Technical Improvements**
- **Smart Classification**: Instant URL/text detection without LLM overhead
- **Specialized Processors**: Direct URL and text processing pipelines
- **Enhanced Tracing**: Detailed performance metadata in LangSmith
- **Comparison Framework**: A/B testing infrastructure for continuous improvement

#### 📖 **Documentation & Tools**
- **User Guide**: LangSmith review process for internal teams
- **Setup Scripts**: Automated evaluation infrastructure initialization
- **Test Harnesses**: Performance comparison and validation tools
- **Architecture Documentation**: Comprehensive refactor plan and implementation guide

#### 🔧 **Configuration**
Enable optimized pipeline:
```bash
export USE_SMART_PIPELINE=true
```

Compare performance:
```bash
python run_comparison_experiment.py
```

### v1.1.0 - Unified Tool Architecture (2025-06-25)

🔧 **Developer Experience Enhancement**: Refactored tool architecture to eliminate code duplication and improve maintainability.

#### ⚡ **Architecture Improvements**
- **Unified Notion Tool**: Single `save_to_notion` tool replaces duplicate `dry_run_save_to_notion`
- **Environment-Driven Behavior**: `DRY_RUN=true/false` controls mock vs real Notion saves
- **Composition Pattern**: Configurable NotionSaver class with shared business logic
- **Code Reduction**: Eliminated 400+ lines of duplicated code

#### 🛠️ **Developer Benefits**
- **Single Source of Truth**: All Notion save logic in one place
- **Easier Testing**: `DRY_RUN=true` enables safe testing without API calls
- **Better Maintainability**: Changes only need to be made in one location
- **LangChain Best Practices**: Follows composition over duplication patterns

Control dry-run mode:
```bash
# Test mode - no actual Notion API calls
export DRY_RUN=true

# Production mode - real Notion saves
export DRY_RUN=false
```

---

## 🏗️ Architectural Improvements TODO

Based on comprehensive architectural review, the following improvements are prioritized for production readiness and scalability:

### 🚨 **Critical (P0) - Production Blockers**

#### 1. **Async-First Architecture** ⏱️
**Issue**: Webhook processing blocks Telegram responses (5s timeout risk)
**Location**: `telegram-bot/main.py:44-49`
```python
# CURRENT: Synchronous blocking
result = process_event_input(raw_input, source, input_type, user_id)

# NEEDED: Async with background tasks
background_tasks.add_task(process_event_async, payload, event_id)
return {"status": "accepted", "event_id": event_id}
```

#### 2. **Unified Error Handling Strategy** 🛡️
**Issue**: Inconsistent error patterns across components
**Impact**: Poor debugging, inconsistent user experience
```python
# NEEDED: Structured error hierarchy
class EventProcessingError(Exception):
    def __init__(self, message: str, error_code: str, retry_after: Optional[int] = None)

class NotionAPIError(EventProcessingError): pass
class ValidationError(EventProcessingError): pass
```

#### 3. **Input Validation Layer** 🔐
**Issue**: No webhook data validation before processing
**Security Risk**: Malformed data can crash processing pipeline
```python
# NEEDED: Pydantic validation models
class TelegramWebhookModel(BaseModel):
    update_id: int = Field(..., gt=0)
    message: Optional[TelegramMessageModel] = None
```

### 🔧 **High Priority (P1) - Scalability Requirements**

#### 4. **Configuration Management** ⚙️
**Issue**: Environment variables scattered throughout codebase
**Solution**: Centralized Pydantic configuration with validation
```python
class AppConfig(BaseSettings):
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    notion_token: str = Field(..., env="NOTION_TOKEN")
    use_smart_pipeline: bool = Field(default=True, env="USE_SMART_PIPELINE")
```

#### 5. **Sophisticated Rate Limiting** ⏱️
**Issue**: Basic Notion API rate limiting without queuing
**Solution**: Redis-based distributed rate limiter with request queuing
```python
class DistributedRateLimiter:
    async def acquire(self, key: str) -> bool:
        # Redis-based rate limiting with queue management
```

#### 6. **Circuit Breaker Pattern** 🔄
**Issue**: No protection against cascading external API failures
**Solution**: Circuit breaker for Notion API calls
```python
class CircuitBreaker:
    # CLOSED → OPEN → HALF_OPEN states
    # Fail fast when external services are down
```

### 📊 **Medium Priority (P2) - Operational Excellence**

#### 7. **Enhanced Monitoring & Observability** 📈
**Current**: Basic LangSmith integration
**Needed**: Comprehensive metrics with Prometheus/Grafana
```python
# Key metrics to track:
webhook_requests_total = Counter('webhook_requests_total', ['source', 'status'])
processing_duration = Histogram('event_processing_seconds', ['event_type'])
notion_api_calls = Counter('notion_api_calls_total', ['endpoint', 'status'])
```

#### 8. **Local Persistence Layer** 💾
**Issue**: Direct dependency on Notion API availability
**Solution**: Local database for event queuing and retry logic
```python
class EventRepository:
    async def save_event(self, event_data: EventModel) -> str:
        # Save locally first, sync to Notion asynchronously
```

#### 9. **Comprehensive Testing Strategy** 🧪
**Current**: Limited test coverage
**Needed**: Unit, integration, and performance tests
```python
# Test categories needed:
# - Unit tests (70%): Individual component testing
# - Integration tests (20%): End-to-end webhook processing
# - Performance tests (10%): Load testing and benchmarks
```

### 🚀 **Low Priority (P3) - Future Enhancements**

#### 10. **Horizontal Scaling Architecture** 📈
**Issue**: Single-process design limits scale
**Solution**: Kubernetes deployment with auto-scaling
```yaml
# kubernetes deployment with:
# - Multiple replicas
# - Resource limits
# - Health checks
# - Auto-scaling based on metrics
```

#### 11. **Advanced Security Measures** 🔒
**Enhancements**: 
- Request signing validation
- Rate limiting per user
- Input sanitization
- Audit logging

#### 12. **Performance Optimizations** ⚡
**Opportunities**:
- Connection pooling for HTTP clients
- Redis caching for repeated operations
- Batch processing for high-volume periods
- Async database operations

### 📋 **Implementation Plan**

**Phase 1 (Week 1-2)**: Critical fixes for production readiness
- [ ] Implement async webhook processing
- [ ] Add unified error handling
- [ ] Create input validation layer
- [ ] Centralize configuration management

**Phase 2 (Week 3-4)**: Scalability improvements
- [ ] Implement sophisticated rate limiting
- [ ] Add circuit breaker pattern
- [ ] Enhanced monitoring and metrics
- [ ] Local persistence layer

**Phase 3 (Week 5-6)**: Production deployment
- [ ] Comprehensive testing suite
- [ ] Kubernetes deployment configuration
- [ ] Security enhancements
- [ ] Performance optimizations

**Success Metrics**:
- Webhook response time < 200ms (currently ~2s)
- 99.9% uptime under load
- Zero webhook timeouts from Telegram
- Horizontal scaling to 10+ instances
- Complete error recovery and retry logic

---

## Roadmap

* [x] **Telegram MVP working end-to-end** ✅
  - ✅ Ability to intake text, photo, and URL
  - ✅ Parse and hydrate based on available context  
  - ✅ Save to Notion
  - ✅ Performance optimization with Smart Pipeline
* [ ] **Production Architecture** (P0 items from TODO above)
* [ ] Cron-based Notion hydrator
* [ ] Add enrichment: venue details, map links
* [ ] Web UI with calendar + filters
* [ ] Add email/Instagram input support
* [ ] Event search flow: user inputs event name -> web fetch known sources + web search engines -> confirm with user via telegram -> validate → save → confirm to user

---

