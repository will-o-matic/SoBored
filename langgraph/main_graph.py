from langgraph.graph import StateGraph, START, END
from utils.state import EventState
from langgraph.nodes import classify_input


def create_event_classifier_graph():
    """
    Create a LangGraph for event classification.
    
    Returns:
        Compiled LangGraph application
    """
    # Step 1: Create the graph
    graph = StateGraph(EventState)
    
    # Step 2: Add the classifier node
    graph.add_node("classifier", classify_input)
    
    # Step 3: Set proper flow: START -> classifier -> END
    graph.add_edge(START, "classifier")
    graph.add_edge("classifier", END)
    
    # Step 4: Compile and return
    return graph.compile()


# Create the compiled application
app = create_event_classifier_graph()
