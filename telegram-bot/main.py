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
        classification = result.get("input_type", "unknown")
        
        # Handle error state
        if classification == "error":
            error_msg = result.get("error", "Unknown error")
            print(f"LangGraph error: {error_msg}")
            classification = "unknown"
        
        # Respond using Telegram sendMessage
        from telegram import Bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=f"Got it! I classified this as: {classification}")
        
    except Exception as e:
        print(f"Error processing message: {e}")
        # Send error response to user
        from telegram import Bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text="Sorry, I encountered an error processing your message.")

    return {"ok": True}
