from langgraph.graph import StateGraph, START, END
from utils.state import EventState
from langgraph.nodes import classify_input, parse_text, respond_to_user


def create_event_processing_graph():
    """
    Create a LangGraph for event processing: Input -> Classify -> Parse -> Respond
    
    Returns:
        Compiled LangGraph application
    """
    # Step 1: Create the graph
    graph = StateGraph(EventState)
    
    # Step 2: Add all nodes
    graph.add_node("classifier", classify_input)
    graph.add_node("parser", parse_text)
    graph.add_node("responder", respond_to_user)
    
    # Step 3: Set up the flow
    graph.add_edge(START, "classifier")
    
    # Conditional edge: only parse text inputs
    def should_parse(state: EventState) -> str:
        if state.input_type == "text":
            return "parser"
        else:
            return "responder"  # Skip parsing for non-text inputs
    
    graph.add_conditional_edges("classifier", should_parse, {
        "parser": "parser",
        "responder": "responder"
    })
    
    # After parsing, always go to responder
    graph.add_edge("parser", "responder")
    graph.add_edge("responder", END)
    
    # Step 4: Compile and return
    return graph.compile()


# Create the compiled application
app = create_event_processing_graph()
