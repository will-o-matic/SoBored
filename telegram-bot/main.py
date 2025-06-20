from fastapi import FastAPI, Request
from pydantic import BaseModel
from langgraph.main_graph import app as langgraph_app
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
    print("received:", message)

    # Prepare raw input for LangGraph classification
    if "photo" in message:
        input_type = "image"  # Pre-classify images since we can detect them from webhook
        raw_input = "[image uploaded]"
    else:
        input_type = None  # Let LangGraph classify text/URLs
        raw_input = text

    # Prepare state for LangGraph
    state = EventState(
        raw_input=raw_input,
        input_type=input_type,
        source="telegram"
    )
    
    try:
        result = langgraph_app.invoke(state)
        
        # Get the formatted response message from the pipeline
        response_message = result.get("response_message", "I processed your message but couldn't generate a response.")
        
        # Handle error state
        if result.get("error"):
            error_msg = result.get("error", "Unknown error")
            print(f"LangGraph error: {error_msg}")
            response_message = "Sorry, I encountered an error processing your message. Please try again."
        
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
