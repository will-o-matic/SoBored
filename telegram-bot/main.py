from fastapi import FastAPI, Request
from pydantic import BaseModel
from langgraph.main_agent import process_event_input
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
    
    print("received:", message)

    # Prepare raw input for LangGraph classification
    if "photo" in message:
        input_type = "image"  # Pre-classify images since we can detect them from webhook
        raw_input = "[image uploaded]"
    else:
        input_type = None  # Let LangGraph classify text/URLs
        raw_input = text

    try:
        # Process the event using the ReAct agent system
        result = process_event_input(
            raw_input=raw_input,
            source="telegram",
            input_type=input_type,
            user_id=user_id
        )
        
        # Extract response from agent output
        if result.get("success"):
            agent_output = result.get("agent_output", "")
            # Create a user-friendly response from the agent output
            if "successfully saved to Notion" in agent_output.lower():
                response_message = "✅ Event processed and saved to Notion!"
            elif "failed" in agent_output.lower() or "error" in agent_output.lower():
                response_message = "⚠️ I processed your message but encountered some issues. Check the details in Notion."
            else:
                response_message = f"📝 Processed your event: {agent_output[:200]}..."
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"Agent error: {error_msg}")
            response_message = "❌ Sorry, I encountered an error processing your message. Please try again."
        
        # Respond using Telegram sendMessage
        from telegram import Bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=response_message, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error processing message: {e}")
        # Send error response to user
        from telegram import Bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text="Sorry, I encountered an error processing your message.")

    return {"ok": True}
