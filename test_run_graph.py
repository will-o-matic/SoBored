import os
from dotenv import load_dotenv
from langgraph.main_graph import app
from utils.state import EventState
from utils.notion_client import get_notion_client, create_events_database_schema

# Load environment variables
load_dotenv()

def test_notion_setup():
    """Test if Notion is properly configured."""
    print("Testing Notion configuration...")
    
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")
    
    if not notion_token:
        print("❌ NOTION_TOKEN not found in environment variables")
        return False
    
    if not database_id:
        print("⚠️  NOTION_DATABASE_ID not found in environment variables")
        print("   Create a database first using create_database_manually()")
        return False
    
    try:
        notion_client = get_notion_client()
        database = notion_client.get_database(database_id)
        if database:
            print("✅ Notion connection successful")
            print(f"   Database: {database.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            return True
        else:
            print("❌ Could not retrieve database")
            return False
    except Exception as e:
        print(f"❌ Notion connection failed: {e}")
        return False

def create_database_manually():
    """Helper to create database manually."""
    print("\n" + "="*50)
    print("MANUAL DATABASE CREATION")
    print("="*50)
    print("To create your events database:")
    print("1. Go to Notion and create a new page")
    print("2. Add your integration to that page (Share > Add connections)")
    print("3. Run this function and provide the page ID")
    print("4. Copy the resulting database ID to your .env file")
    
    parent_page_id = input("\nEnter the Page ID where you want to create the database: ").strip()
    
    if not parent_page_id:
        print("No page ID provided, skipping database creation")
        return
    
    try:
        notion_client = get_notion_client()
        schema = create_events_database_schema()
        
        print("Creating events database...")
        database = notion_client.create_database(
            parent_page_id=parent_page_id,
            title="SoBored Events",
            properties=schema
        )
        
        if database:
            database_id = database['id']
            print(f"✅ Database created successfully!")
            print(f"Database ID: {database_id}")
            print(f"\n📝 Add this to your .env file:")
            print(f"NOTION_DATABASE_ID={database_id}")
        else:
            print("❌ Failed to create database")
            
    except Exception as e:
        print(f"Error: {e}")

def test_langgraph_with_notion():
    """Test the full LangGraph pipeline including Notion integration."""
    print("\nTesting LangGraph with Notion integration...")
    
    # Example 1: plain text
    print("\n1. Testing plain text with Notion save:")
    state = EventState(
        raw_input="Concert at Golden Gate Park this Saturday at 7pm",
        source="telegram"
    )
    result = app.invoke(state)
    print("Input:", state.raw_input)
    print("Classified as:", result.input_type)
    print("Notion status:", result.notion_save_status)
    if result.notion_url:
        print("Notion URL:", result.notion_url)
    if result.response_message:
        print("Response:", result.response_message)

    # Example 2: URL
    print("\n2. Testing URL with Notion save:")
    state2 = EventState(
        raw_input="https://eventbrite.com/some-event",
        source="telegram"
    )
    result2 = app.invoke(state2)
    print("Input:", state2.raw_input)
    print("Classified as:", result2.input_type)
    print("Notion status:", result2.notion_save_status)
    if result2.notion_url:
        print("Notion URL:", result2.notion_url)
    if result2.response_message:
        print("Response:", result2.response_message)

    # Example 3: image
    print("\n3. Testing image with Notion save:")
    state3 = EventState(
        raw_input="[event flyer image]",
        input_type="image",
        source="telegram"
    )
    result3 = app.invoke(state3)
    print("Input:", state3.raw_input)
    print("Classified as:", result3.input_type)
    print("Notion status:", result3.notion_save_status)
    if result3.notion_url:
        print("Notion URL:", result3.notion_url)
    if result3.response_message:
        print("Response:", result3.response_message)

if __name__ == "__main__":
    print("SoBored Event Aggregator - Test Suite")
    print("=" * 40)
    
    # Test Notion setup first
    notion_ready = test_notion_setup()
    
    if not notion_ready and os.environ.get("NOTION_TOKEN"):
        # Offer to create database
        create_db = input("\nWould you like to create the database now? (y/n): ").lower().strip()
        if create_db == 'y':
            create_database_manually()
            print("\nRerun this script after adding the database ID to .env")
            exit()
    
    if notion_ready:
        test_langgraph_with_notion()
    else:
        print("\n⚠️  Skipping LangGraph tests - Notion not properly configured")
        print("   Set up Notion first, then rerun this script")
    
    print("\nTest completed!")

