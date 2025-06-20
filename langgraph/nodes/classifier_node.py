import re
from utils.state import EventState

def classify_input(state: EventState) -> EventState:
    content = state.raw_input or ""

    # Check for image separately (Telegram would pass metadata in the webhook)
    if state.input_type == "image":
        state.input_type = "image"
    elif re.search(r'https?://\S+', content):
        state.input_type = "url"
    elif content.strip():
        state.input_type = "text"
    else:
        state.input_type = "unknown"

    return state
