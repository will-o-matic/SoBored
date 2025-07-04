from fastapi import FastAPI, Request
from pydantic import BaseModel
from langgraph.main_agent import process_event_input
from langgraph.observability.structured_logging import TelegramAgentLogger
from utils.state import EventState
import os
from dotenv import load_dotenv

app = FastAPI()

class TelegramMessage(BaseModel):
    update_id: int
    message: dict

@app.post("/telegram/webhook")
async def handle_webhook(payload: TelegramMessage):
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    message = payload.message
    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    
    # Extract user ID for Notion integration
    user_id = str(chat_id)  # Use chat_id as user_id for Telegram
    
    # Initialize Telegram-specific logger
    telegram_logger = TelegramAgentLogger(user_id=user_id, chat_id=str(chat_id))
    
    print("received:", message)

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
    with telegram_logger.track_message_processing(raw_input) as session_id:
        try:
            # Process the event using the ReAct agent system
            result = process_event_input(
                raw_input=raw_input,
                source="telegram",
                input_type=input_type,
                user_id=user_id,
                telegram_data=telegram_data  # Pass Telegram image data if available
            )
            
            # Extract response from agent output - handle both ReAct agent and Smart Pipeline
            processing_method = result.get("processing_method", "unknown")
            
            # Check for successful processing (different formats for different systems)
            success_indicators = [
                result.get("success"),  # ReAct agent format
                result.get("notion_save_status") == "success",  # Smart Pipeline format
                "notion_page_id" in result and result.get("notion_page_id")  # Alternative success check
            ]
            
            # Check if confirmation is required (for image processing)
            if result.get("confirmation_required", False):
                confirmation_message = result.get("confirmation_message", "")
                if confirmation_message:
                    response_message = confirmation_message
                else:
                    response_message = "📋 Please confirm the extracted event details before saving."
                
                # Store pending confirmation data for this user
                # TODO: Implement proper session storage (Redis, database, etc.)
                # For now, just send the confirmation message
                
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
            from telegram import Bot
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=chat_id, text=response_message, parse_mode="Markdown")
            
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

    return {"ok": True}
