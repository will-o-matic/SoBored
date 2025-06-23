"""
Structured logging configuration for the SoBored event agent system.
"""

import os
import structlog
import logging
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager


def configure_structured_logging():
    """Configure structured logging based on environment."""
    
    # Determine environment
    environment = os.getenv("ENVIRONMENT", "development").lower()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    if environment == "production":
        # Production: JSON logs for log aggregation
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: Human-readable logs
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, log_level, logging.INFO),
    )
    
    print(f"[LOGGING] Configured structured logging - Environment: {environment}, Level: {log_level}")


class ReActAgentLogger:
    """Structured logger for ReAct agent operations."""
    
    def __init__(self, agent_name: str = "event_processor"):
        self.logger = structlog.get_logger().bind(
            component="react_agent",
            agent_name=agent_name
        )
    
    def log_agent_invocation_start(
        self, 
        user_id: Optional[str] = None,
        source: str = "unknown",
        raw_input: str = "",
        session_id: Optional[str] = None
    ):
        """Log the start of agent processing."""
        self.logger.info(
            "Agent processing started",
            event_type="agent_start",
            user_id=user_id,
            source=source,
            raw_input=raw_input[:100] + "..." if len(raw_input) > 100 else raw_input,
            session_id=session_id
        )
    
    def log_agent_invocation_end(
        self,
        user_id: Optional[str] = None,
        source: str = "unknown",
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
        session_id: Optional[str] = None
    ):
        """Log the end of agent processing."""
        log_data = {
            "event_type": "agent_end",
            "user_id": user_id,
            "source": source,
            "success": success,
            "session_id": session_id
        }
        
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms
        
        if success:
            self.logger.info("Agent processing completed", **log_data)
        else:
            log_data["error"] = error
            self.logger.error("Agent processing failed", **log_data)
    
    def log_tool_execution(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None
    ):
        """Log tool execution details."""
        log_data = {
            "event_type": "tool_execution",
            "tool_name": tool_name,
            "inputs": inputs,
            "success": success
        }
        
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms
        
        if success and outputs:
            log_data["outputs"] = outputs
            self.logger.info("Tool execution completed", **log_data)
        elif not success:
            log_data["error"] = error
            self.logger.error("Tool execution failed", **log_data)
        else:
            self.logger.info("Tool execution completed", **log_data)
    
    def log_reasoning_step(
        self,
        step_number: int,
        thought: str,
        action: str,
        action_input: str,
        observation: str = ""
    ):
        """Log ReAct reasoning step."""
        self.logger.debug(
            "ReAct reasoning step",
            event_type="reasoning_step",
            step_number=step_number,
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation
        )
    
    def log_notion_operation(
        self,
        operation: str,
        event_data: Dict[str, Any],
        success: bool,
        error: Optional[str] = None,
        notion_page_id: Optional[str] = None
    ):
        """Log Notion database operations."""
        log_data = {
            "event_type": "notion_operation",
            "operation": operation,
            "event_title": event_data.get("title", "Unknown"),
            "success": success
        }
        
        if success and notion_page_id:
            log_data["notion_page_id"] = notion_page_id
            self.logger.info("Notion operation completed", **log_data)
        elif not success:
            log_data["error"] = error
            log_data["event_data"] = event_data
            self.logger.error("Notion operation failed", **log_data)
        else:
            self.logger.info("Notion operation completed", **log_data)
    
    def log_telegram_event(
        self,
        event_type: str,
        user_id: str,
        chat_id: str,
        message: str = "",
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log Telegram-specific events."""
        log_data = {
            "event_type": "telegram_event",
            "telegram_event_type": event_type,
            "user_id": user_id,
            "chat_id": chat_id,
            "success": success
        }
        
        if message:
            log_data["message"] = message[:100] + "..." if len(message) > 100 else message
        
        if success:
            self.logger.info("Telegram event processed", **log_data)
        else:
            log_data["error"] = error
            self.logger.error("Telegram event failed", **log_data)


class TelegramAgentLogger(ReActAgentLogger):
    """Specialized logger for Telegram agent interactions."""
    
    def __init__(self, user_id: str, chat_id: str):
        super().__init__(agent_name="telegram_event_processor")
        self.logger = self.logger.bind(
            user_id=user_id,
            chat_id=chat_id,
            source="telegram"
        )
    
    @contextmanager
    def track_message_processing(self, message: str):
        """Context manager to track message processing with timing."""
        start_time = time.time()
        session_id = f"tg_{self.logger._context.get('user_id', 'unknown')}_{int(start_time)}"
        
        self.log_agent_invocation_start(
            user_id=self.logger._context.get('user_id'),
            source="telegram",
            raw_input=message,
            session_id=session_id
        )
        
        try:
            yield session_id
            duration_ms = (time.time() - start_time) * 1000
            self.log_agent_invocation_end(
                user_id=self.logger._context.get('user_id'),
                source="telegram",
                success=True,
                duration_ms=duration_ms,
                session_id=session_id
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_agent_invocation_end(
                user_id=self.logger._context.get('user_id'),
                source="telegram",
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                session_id=session_id
            )
            raise


def get_logger(name: str = "sobored") -> structlog.stdlib.BoundLogger:
    """Get a configured structured logger."""
    return structlog.get_logger(name)


# Initialize logging configuration when module is imported
configure_structured_logging()