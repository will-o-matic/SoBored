from langgraph.graph import StateGraph, START, END
from utils.state import EventState
from langgraph.nodes import classify_input, parse_text, respond_to_user, save_to_notion, fetch_url_content, parse_url_content


def create_event_processing_graph():
    """
    Create a LangGraph for event processing: Input -> Classify -> Fetch/Parse -> Save to Notion -> Respond
    
    Returns:
        Compiled LangGraph application
    """
    # Step 1: Create the graph
    graph = StateGraph(EventState)
    
    # Step 2: Add all nodes
    graph.add_node("classifier", classify_input)
    graph.add_node("parser", parse_text)
    graph.add_node("url_fetcher", fetch_url_content)
    graph.add_node("url_parser", parse_url_content)
    graph.add_node("notion_saver", save_to_notion)
    graph.add_node("responder", respond_to_user)
    
    # Step 3: Set up the flow
    graph.add_edge(START, "classifier")
    
    # Conditional edge: route based on input type
    def route_after_classification(state: EventState) -> str:
        if state.input_type == "text":
            return "parser"
        elif state.input_type == "url":
            return "url_fetcher"
        else:
            return "notion_saver"  # Skip parsing for other inputs, go directly to Notion
    
    graph.add_conditional_edges("classifier", route_after_classification, {
        "parser": "parser",
        "url_fetcher": "url_fetcher",
        "notion_saver": "notion_saver"
    })
    
    # After text parsing, save to Notion
    graph.add_edge("parser", "notion_saver")
    
    # After URL fetching, parse the webpage content
    graph.add_edge("url_fetcher", "url_parser")
    
    # After URL parsing, save to Notion
    graph.add_edge("url_parser", "notion_saver")
    
    # After saving to Notion, respond to user
    graph.add_edge("notion_saver", "responder")
    graph.add_edge("responder", END)
    
    # Step 4: Compile and return
    return graph.compile()


# Create the compiled application
app = create_event_processing_graph()
