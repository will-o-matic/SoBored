from langgraph.main_graph import app
from utils.state import EventState

print("Testing improved LangGraph implementation...")

# Example 1: plain text
print("\n1. Testing plain text classification:")
state = EventState(
    raw_input="DJ set at Monarch this Saturday!",
    source="manual"
)
result = app.invoke(state)
print("Input:", state.raw_input)
print("Classified as:", result["input_type"])

# Example 2: URL
print("\n2. Testing URL classification:")
state2 = EventState(
    raw_input="https://sf.fun/things-to-do",
    source="manual"
)
result2 = app.invoke(state2)
print("Input:", state2.raw_input)
print("Classified as:", result2["input_type"])

# Example 3: image (would come with input_type set ahead of time)
print("\n3. Testing image classification:")
state3 = EventState(
    raw_input="[image uploaded]",
    input_type="image",
    source="manual"
)
result3 = app.invoke(state3)
print("Input:", state3.raw_input)
print("Classified as:", result3["input_type"])

# Example 4: empty input
print("\n4. Testing empty input:")
state4 = EventState(
    raw_input="",
    source="manual"
)
result4 = app.invoke(state4)
print("Input:", repr(state4.raw_input))
print("Classified as:", result4["input_type"])

print("\nAll tests completed successfully!")

