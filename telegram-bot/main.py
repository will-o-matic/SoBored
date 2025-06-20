from fastapi import FastAPI, Request
from pydantic import BaseModel
from langgraph.main_graph import app as langgraph_app
from utils.state import EventState

app = FastAPI()

class TelegramMessage(BaseModel):
    update_id: int
    message: dict

@app.post("/telegram/webhook")
async def handle_webhook(payload: TelegramMessage):
    message = payload.message
    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    print("received:", message)

    # Detect image type (simplified, assumes no mixed media)
    if "photo" in message:
        input_type = "image"
        raw_input = "[image uploaded]"
    elif text.startswith("http"):
        input_type = "url"
        raw_input = text
    else:
        input_type = "text"
        raw_input = text

    # Prepare state for LangGraph
    state = EventState(
        raw_input=raw_input,
        input_type=input_type,
        source="telegram"
    )
    result = langgraph_app.invoke(state)
    classification = result["input_type"]

    # Respond using Telegram sendMessage
    from telegram import Bot
    bot = Bot(token="8057932135:AAHqN_iWcqScAKhtNcFlE7C44IlQi_9S4Xc")
    await bot.send_message(chat_id=chat_id, text=f"Got it! I classified this as: {classification}")

    return {"ok": True}
