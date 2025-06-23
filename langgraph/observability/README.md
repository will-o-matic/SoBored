# SoBored Agent Observability Guide

This document explains how to configure logging and observability for the SoBored event processing system.

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Add these variables to your `.env` file:

```bash
# LangSmith Configuration (Optional)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=sobored-event-agent

# Logging Configuration
ENVIRONMENT=development  # or 'production'
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Required for main functionality
ANTHROPIC_API_KEY=your-anthropic-api-key
TELEGRAM_BOT_TOKEN=your-telegram-token
NOTION_TOKEN=your-notion-integration-token
NOTION_DATABASE_ID=your-notion-database-id
```

## LangSmith Integration

LangSmith provides visual debugging and monitoring for your ReAct agents.

### Benefits
- **Visual agent debugging** - See reasoning steps in a web interface
- **Performance monitoring** - Track latency, token usage, and costs
- **Error tracking** - Detailed error traces and debugging
- **Production monitoring** - Dashboards for system health

### Setup Steps

1. **Get LangSmith API Key**
   - Sign up at [smith.langchain.com](https://smith.langchain.com)
   - Create a new project
   - Copy your API key

2. **Configure Environment**
   ```bash
   export LANGSMITH_TRACING=true
   export LANGSMITH_API_KEY=your-api-key
   export LANGSMITH_PROJECT=your-project-name
   ```

3. **Verify Setup**
   Run any agent command - traces will appear in your LangSmith dashboard.

### Cost Considerations
- Free tier: 5,000 traces/month
- Paid plans: $39/month for 100k traces
- Filter sensitive data before tracing

## Structured Logging

The system uses structured logging for production monitoring and debugging.

### Log Formats

**Development** (human-readable):
```
2024-01-15 10:30:45 [INFO] Agent processing started user_id=123 source=telegram
```

**Production** (JSON for log aggregation):
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "message": "Agent processing started",
  "user_id": "123",
  "source": "telegram",
  "event_type": "agent_start"
}
```

### Log Levels

- **DEBUG**: Detailed ReAct reasoning steps, tool inputs/outputs
- **INFO**: Agent invocations, tool executions, successful operations
- **WARNING**: Recoverable errors, fallback operations
- **ERROR**: Failed operations, tool errors
- **CRITICAL**: System failures, unrecoverable errors

### Key Events Logged

1. **Agent Sessions**
   - Session start/end with timing
   - Success/failure status
   - User context (Telegram user ID, source)

2. **Tool Executions**
   - Tool name and inputs
   - Execution duration
   - Success/failure with outputs or errors

3. **Notion Operations**
   - Event saves to Notion
   - Database operations
   - API response status

4. **Telegram Events**
   - Message processing start/end
   - User interactions
   - Webhook errors

## Environment Configuration

### Development Setup
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
LANGSMITH_TRACING=true
```

**Features:**
- Human-readable console logs
- All debug information visible
- LangSmith tracing enabled
- Verbose agent reasoning

### Production Setup
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
LANGSMITH_TRACING=false  # or true with cost consideration
```

**Features:**
- JSON structured logs
- Optimized for log aggregation
- Reduced verbosity
- Performance monitoring focus

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Agent Performance**
   - Average processing time per message
   - Success/failure rates
   - Tool execution latencies

2. **User Activity**
   - Messages processed per hour/day
   - User engagement patterns
   - Error rates by user

3. **System Health**
   - Notion API response times
   - Telegram webhook reliability
   - Memory and CPU usage

### Log Analysis Queries

**Find failed agent executions:**
```json
{
  "event_type": "agent_end",
  "success": false
}
```

**Monitor Notion save operations:**
```json
{
  "event_type": "notion_operation",
  "operation": "create_page"
}
```

**Track user activity:**
```json
{
  "source": "telegram",
  "user_id": "specific_user_id"
}
```

## Troubleshooting

### Common Issues

1. **LangSmith not tracing**
   - Check `LANGSMITH_TRACING=true`
   - Verify API key is correct
   - Ensure `langsmith` package is installed

2. **No structured logs appearing**
   - Check `LOG_LEVEL` setting
   - Verify imports in agent code
   - Ensure structlog is configured

3. **Performance issues**
   - Lower log level in production
   - Disable debug logging
   - Consider async logging for high volume

### Debug Commands

**Test logging configuration:**
```python
from langgraph.observability.structured_logging import get_logger
logger = get_logger("test")
logger.info("Test log message", test_field="test_value")
```

**Test LangSmith configuration:**
```python
from langgraph.observability.langsmith_config import configure_langsmith
configured = configure_langsmith()
print(f"LangSmith configured: {configured}")
```

## Integration Examples

### Custom Tool Logging
```python
from langgraph.observability.structured_logging import ReActAgentLogger

logger = ReActAgentLogger("custom_tool")

def my_custom_tool(input_data):
    start_time = time.time()
    try:
        result = process_data(input_data)
        duration_ms = (time.time() - start_time) * 1000
        
        logger.log_tool_execution(
            tool_name="my_custom_tool",
            inputs={"data": input_data},
            outputs={"result": result},
            success=True,
            duration_ms=duration_ms
        )
        return result
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.log_tool_execution(
            tool_name="my_custom_tool",
            inputs={"data": input_data},
            success=False,
            error=str(e),
            duration_ms=duration_ms
        )
        raise
```

### Production Monitoring Script
```python
import structlog
from datetime import datetime, timedelta

# Query logs for errors in last hour
logger = structlog.get_logger()
one_hour_ago = datetime.now() - timedelta(hours=1)

# This would integrate with your log aggregation system
error_count = count_logs({
    "level": "error",
    "timestamp": {"gte": one_hour_ago.isoformat()},
    "component": "react_agent"
})

if error_count > 10:
    logger.critical("High error rate detected", error_count=error_count)
    # Trigger alert system
```

## Next Steps

1. **Set up log aggregation** (ELK stack, Datadog, etc.)
2. **Create monitoring dashboards** for key metrics
3. **Configure alerting** for critical errors
4. **Implement log retention policies**
5. **Add custom metrics** for business KPIs