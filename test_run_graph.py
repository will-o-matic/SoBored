from langgraph.main_graph import app
from utils.state import EventState

# Example 1: plain text
state = EventState(
    raw_input="DJ set at Monarch this Saturday!",
    source="manual"
)
result = app.invoke(state)
print("Classified as:", result["input_type"])

# Example 2: URL
state2 = EventState(
    raw_input="https://sf.fun/things-to-do",
    source="manual"
)
result2 = app.invoke(state2)
print("Classified as:", result2["input_type"])


# Example 3: image (would come with input_type set ahead of time)
state3 = EventState(
    raw_input=None,
    input_type="image",
    source="manual"
)
result3 = app.invoke(state3)
print("Classified as:", result3["input_type"])

