import sys
import os
import time
# Add parent directory to Python path so we can import langgraph modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from langgraph.main_agent import process_event_input
from langgraph.observability.structured_logging import TelegramAgentLogger
from utils.state import EventState
from dotenv import load_dotenv
import asyncio

app = FastAPI()

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        print(f"[MIDDLEWARE] Request started at {start_time:.3f} for {request.url.path}")
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        print(f"[MIDDLEWARE] Request completed in {duration:.3f}s for {request.url.path}")
        
        return response

app.add_middleware(TimingMiddleware)

class TelegramMessage(BaseModel):
    update_id: int
    message: dict

@app.post("/telegram/webhook")
async def handle_webhook(payload: TelegramMessage):
    webhook_start = time.time()
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    message = payload.message
    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    
    # Extract user ID for Notion integration
    user_id = str(chat_id)  # Use chat_id as user_id for Telegram
    
    # Initialize Telegram-specific logger
    telegram_logger = TelegramAgentLogger(user_id=user_id, chat_id=str(chat_id))
    
    print(f"[TIMING] Webhook received at {time.time():.3f}")
    print("received:", message)

    # Import session manager for confirmation handling
    from utils.session_manager import session_manager, is_confirmation_response, parse_confirmation_response
    
    # Check if this is a confirmation response to a pending confirmation
    if text and is_confirmation_response(text):
        print(f"[DEBUG] Detected confirmation response: '{text}' from user {user_id}")
        print(f"[DEBUG] Session manager has {session_manager.get_session_count()} active sessions")
        pending_confirmation = session_manager.get_pending_confirmation(user_id, str(chat_id))
        print(f"[DEBUG] Retrieved pending confirmation: {pending_confirmation is not None}")
        
        if pending_confirmation:
            # This is a confirmation response - handle it specially
            confirmation_response = parse_confirmation_response(text)
            
            if confirmation_response['action'] == 'confirm':
                # User confirmed - proceed with saving the pending event data
                event_data = session_manager.confirm_and_remove(user_id, str(chat_id))
                
                if event_data:
                    # Use context manager for tracking confirmation processing
                    with telegram_logger.track_message_processing(f"[confirmation: yes] {text}") as session_id:
                        try:
                            # Save the confirmed event data directly
                            from langgraph.agents.tools.save_notion_tool import save_to_notion
                            
                            result = save_to_notion.invoke({
                                "input_type": event_data.get("input_type", "image"),
                                "raw_input": event_data.get("raw_input", "[confirmed event]"),
                                "source": event_data.get("source", "telegram"),
                                "event_title": event_data.get("event_title"),
                                "event_date": event_data.get("event_date"),
                                "event_location": event_data.get("event_location"),
                                "event_description": event_data.get("event_description"),
                                "user_id": user_id
                            })
                            
                            # Format success response
                            if result.get("notion_save_status") == "success":
                                event_title = event_data.get("event_title", "Event")
                                notion_url = result.get("notion_url", "")
                                
                                if notion_url:
                                    response_message = f"✅ Event confirmed and saved: **{event_title}**\n[View in Notion]({notion_url})"
                                else:
                                    response_message = f"✅ Event confirmed and saved: **{event_title}**"
                                
                                # Log successful confirmation
                                telegram_logger.log_telegram_event(
                                    event_type="confirmation_processed",
                                    user_id=user_id,
                                    chat_id=str(chat_id),
                                    message=text,
                                    success=True
                                )
                            else:
                                response_message = "❌ Event confirmed but failed to save to Notion. Please try again."
                                
                        except Exception as e:
                            print(f"Error saving confirmed event: {e}")
                            response_message = "❌ Error saving confirmed event. Please try again."
                
                else:
                    response_message = "❌ Confirmation data was lost. Please try uploading the image again."
                    
            elif confirmation_response['action'] == 'cancel':
                # User cancelled - remove pending confirmation
                session_manager.cancel_confirmation(user_id, str(chat_id))
                response_message = "❌ Event cancelled. You can upload another image to try again."
                
            elif confirmation_response['action'] == 'edit':
                # User wants to edit a field - update pending confirmation
                field = confirmation_response['field']
                value = confirmation_response['value']
                
                pending_confirmation.event_data[f"event_{field}"] = value
                session_manager.store_pending_confirmation(
                    user_id, str(chat_id), 
                    pending_confirmation.event_data,
                    pending_confirmation.confirmation_message
                )
                
                response_message = f"✏️ Updated {field} to: {value}\n\nPlease confirm again with 'Yes' or make more edits."
                
            else:
                response_message = "❓ I didn't understand that response. Please reply with:\n✅ 'Yes' to confirm\n❌ 'Cancel' to discard\n✏️ 'field: new value' to edit"
            
            # Send response and return early
            print(f"[TIMING] Sending confirmation response at {time.time():.3f}")
            from telegram import Bot
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=chat_id, text=response_message, parse_mode="Markdown")
            print(f"[TIMING] Webhook completed (confirmation) at {time.time():.3f}, total: {time.time() - webhook_start:.3f}s")
            return {"ok": True}

    # Prepare raw input for LangGraph classification
    if "photo" in message:
        input_type = "image"  # Pre-classify images since we can detect them from webhook
        raw_input = "[image uploaded]"
        
        # Add image metadata for processing
        telegram_data = {
            "photo": message["photo"],
            "chat_id": chat_id,
            "message_id": message.get("message_id"),
            "caption": message.get("caption", "")  # Image caption if provided
        }
    else:
        input_type = None  # Let LangGraph classify text/URLs
        raw_input = text
        telegram_data = None

    # Use context manager for tracking message processing
    print(f"[TIMING] Starting agent processing at {time.time():.3f}")
    with telegram_logger.track_message_processing(raw_input) as session_id:
        try:
            # Process the event using the ReAct agent system
            agent_start = time.time()
            
            # Monitor for long-running synchronous operations
            print(f"[ASYNC] Creating task at {time.time():.3f}")
            
            # Create a wrapper function for proper keyword argument handling
            def process_with_kwargs():
                return process_event_input(
                    raw_input=raw_input,
                    source="telegram",
                    input_type=input_type,
                    user_id=user_id,
                    telegram_data=telegram_data  # Pass Telegram image data if available
                )
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, process_with_kwargs)
            
            print(f"[TIMING] Agent processing completed at {time.time():.3f}, duration: {time.time() - agent_start:.3f}s")
            
            # Debug: Print the complete result to understand what's being returned
            print(f"[DEBUG] Complete result: {result}")
            
            # Extract response from agent output - handle both ReAct agent and Smart Pipeline
            processing_method = result.get("processing_method", "unknown")
            
            # Check for successful processing (different formats for different systems)
            success_indicators = [
                result.get("success"),  # ReAct agent format
                result.get("notion_save_status") == "success",  # Smart Pipeline format
                "notion_page_id" in result and result.get("notion_page_id")  # Alternative success check
            ]
            
            # Check if confirmation is required (for image processing)
            print(f"[DEBUG] Checking confirmation_required: {result.get('confirmation_required', False)}")
            if result.get("confirmation_required", False):
                confirmation_message = result.get("confirmation_message", "")
                if confirmation_message:
                    response_message = confirmation_message
                else:
                    response_message = "📋 Please confirm the extracted event details before saving."
                
                # Store pending confirmation data for this user
                event_data = {
                    "input_type": input_type,
                    "raw_input": raw_input,
                    "source": "telegram",
                    "event_title": result.get("event_title"),
                    "event_date": result.get("event_date"),
                    "event_location": result.get("event_location"),
                    "event_description": result.get("event_description")
                }
                
                print(f"[DEBUG] Storing session data: {event_data}")
                store_start = time.time()
                session_manager.store_pending_confirmation(
                    user_id=user_id,
                    chat_id=str(chat_id),
                    event_data=event_data,
                    confirmation_message=confirmation_message,
                    ttl_seconds=300  # 5 minutes
                )
                print(f"[TIMING] Session storage at {time.time():.3f}, duration: {time.time() - store_start:.3f}s")
                print(f"[CONFIRMATION] Stored pending event data for user {user_id}")
                print(f"[DEBUG] Session manager now has {session_manager.get_session_count()} active sessions")
                
            elif any(success_indicators) and not result.get("error"):
                # Extract meaningful information for user response
                event_title = result.get("event_title", "")
                notion_url = result.get("notion_url", "")
                total_sessions = result.get("total_sessions")
                
                if event_title:
                    if notion_url:
                        response_message = f"✅ Event saved: **{event_title}**\n[View in Notion]({notion_url})"
                    else:
                        response_message = f"✅ Event saved: **{event_title}**"
                else:
                    response_message = "✅ Event processed and saved to Notion!"
                
                # Add multi-instance info
                if total_sessions and total_sessions > 1:
                    response_message += f"\n📅 Created {total_sessions} separate sessions with series linking"
                
                # Add processing method info for debugging
                if processing_method == "smart_pipeline":
                    processing_time = result.get("processing_time", 0)
                    response_message += f"\n⚡ Processed in {processing_time:.1f}s with Smart Pipeline"
                
                # Log successful Telegram event
                telegram_logger.log_telegram_event(
                    event_type="message_processed",
                    user_id=user_id,
                    chat_id=str(chat_id),
                    message=raw_input,
                    success=True
                )
            else:
                error_msg = result.get("error", "Processing failed")
                print(f"Processing error ({processing_method}): {error_msg}")
                
                # More specific error messages based on the type of failure
                if "notion" in error_msg.lower():
                    response_message = "⚠️ Event was processed but couldn't be saved to Notion. Please try again."
                elif "fetch" in error_msg.lower() or "url" in error_msg.lower():
                    response_message = "⚠️ Couldn't access that URL. Please check the link and try again."
                elif "parse" in error_msg.lower():
                    response_message = "⚠️ Couldn't extract event details from that content. Try providing more specific information."
                else:
                    response_message = "❌ Sorry, I encountered an error processing your message. Please try again."
                
                # Log failed Telegram event
                telegram_logger.log_telegram_event(
                    event_type="message_processed",
                    user_id=user_id,
                    chat_id=str(chat_id),
                    message=raw_input,
                    success=False,
                    error=error_msg
                )
            
            # Respond using Telegram sendMessage
            print(f"[TIMING] Sending response at {time.time():.3f}")
            telegram_start = time.time()
            from telegram import Bot
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=chat_id, text=response_message, parse_mode="Markdown")
            print(f"[TIMING] Telegram API call completed at {time.time():.3f}, duration: {time.time() - telegram_start:.3f}s")
            
        except Exception as e:
            print(f"Error processing message: {e}")
            
            # Log exception
            telegram_logger.log_telegram_event(
                event_type="webhook_error",
                user_id=user_id,
                chat_id=str(chat_id),
                message=raw_input,
                success=False,
                error=str(e)
            )
            
            # Send error response to user
            from telegram import Bot
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=chat_id, text="Sorry, I encountered an error processing your message.")

    print(f"[TIMING] Webhook completed at {time.time():.3f}, total: {time.time() - webhook_start:.3f}s")
    return {"ok": True}
