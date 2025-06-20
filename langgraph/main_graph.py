from langgraph.graph import StateGraph
from utils.state import EventState
from langgraph.nodes import classifier_node 


# Step 1: Create the graph
graph = StateGraph(EventState)

# Step 2: Add the classifier node
graph.add_node("classifier", classifier_node.classify_input)

# Step 3: Set start + flow
graph.set_entry_point("classifier")
graph.set_finish_point("classifier")  # no further processing yet

# Step 4: Compile it
app = graph.compile()
