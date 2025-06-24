#!/usr/bin/env python3
"""
Update Notion Database Schema for Multi-Date Support

This script updates the existing Notion database to include new properties
needed for multi-date event series functionality.

New fields added:
- Series ID: Links related events in a multi-session series
- Session Number: Which session this is (1, 2, 3, etc.)
- Total Sessions: Total number of sessions in the series
- Recurrence: For future RRULE support (recurring events)

Usage:
    python update_notion_schema.py [--dry-run] [--database-id DATABASE_ID]
"""

import os
import argparse
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from utils.notion_client import NotionClientWrapper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_updated_schema_properties() -> Dict[str, Any]:
    """
    Get the new properties to add to the database schema
    
    Returns:
        Dict containing new property definitions
    """
    return {
        "Series ID": {
            "rich_text": {},
            "description": "Unique identifier linking events in a multi-session series"
        },
        "Session Number": {
            "number": {
                "format": "number"
            },
            "description": "Which session this is in the series (1, 2, 3, etc.)"
        },
        "Total Sessions": {
            "number": {
                "format": "number"
            },
            "description": "Total number of sessions in this series"
        },
        "Recurrence": {
            "rich_text": {},
            "description": "RFC 5545 RRULE for recurring events (future feature)"
        }
    }


def get_full_updated_schema() -> Dict[str, Any]:
    """
    Get the complete updated database schema including existing and new fields
    
    Returns:
        Dict containing complete schema definition
    """
    # Start with existing schema
    schema = {
        "Title": {
            "title": {}
        },
        "Date/Time": {
            "date": {}
        },
        "Location": {
            "rich_text": {}
        },
        "Description": {
            "rich_text": {}
        },
        "Source": {
            "select": {
                "options": [
                    {"name": "telegram", "color": "blue"},
                    {"name": "web", "color": "green"},
                    {"name": "email", "color": "yellow"},
                    {"name": "instagram", "color": "pink"},
                    {"name": "pipeline", "color": "purple"}  # Added for Smart Pipeline
                ]
            }
        },
        "URL": {
            "url": {}
        },
        "Classification": {
            "select": {
                "options": [
                    {"name": "event", "color": "purple"},
                    {"name": "url", "color": "orange"},
                    {"name": "text", "color": "gray"},
                    {"name": "image", "color": "red"},
                    {"name": "unknown", "color": "default"}
                ]
            }
        },
        "Status": {
            "select": {
                "options": [
                    {"name": "new", "color": "yellow"},
                    {"name": "processed", "color": "green"},
                    {"name": "archived", "color": "gray"}
                ]
            }
        },
        "UserId": {
            "rich_text": {}
        },
        "Added": {
            "date": {}
        }
    }
    
    # Add new multi-date properties
    schema.update(get_updated_schema_properties())
    
    return schema


def check_current_schema(notion_client: NotionClientWrapper, database_id: str) -> Optional[Dict[str, Any]]:
    """
    Check the current database schema
    
    Args:
        notion_client: Notion client instance
        database_id: Database ID to check
        
    Returns:
        Current database schema or None if error
    """
    try:
        database = notion_client.get_database(database_id)
        if not database:
            return None
            
        current_properties = database.get('properties', {})
        print(f"📊 Current database has {len(current_properties)} properties:")
        
        for prop_name, prop_config in current_properties.items():
            prop_type = prop_config.get('type', 'unknown')
            print(f"  • {prop_name} ({prop_type})")
            
        return current_properties
        
    except Exception as e:
        logger.error(f"Failed to check current schema: {e}")
        return None


def update_database_schema(notion_client: NotionClientWrapper, database_id: str, dry_run: bool = False) -> bool:
    """
    Update the database schema with new multi-date properties
    
    Args:
        notion_client: Notion client instance
        database_id: Database ID to update
        dry_run: If True, only show what would be updated
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current schema
        print("🔍 Checking current database schema...")
        current_properties = check_current_schema(notion_client, database_id)
        if current_properties is None:
            return False
        
        # Get new properties to add
        new_properties = get_updated_schema_properties()
        
        # Check which properties need to be added
        properties_to_add = {}
        for prop_name, prop_config in new_properties.items():
            if prop_name not in current_properties:
                properties_to_add[prop_name] = prop_config
                
        if not properties_to_add:
            print("✅ Database schema is already up to date!")
            return True
            
        print(f"\n🔧 Need to add {len(properties_to_add)} new properties:")
        for prop_name, prop_config in properties_to_add.items():
            prop_type = prop_config.get('type', list(prop_config.keys())[0])
            description = prop_config.get('description', '')
            print(f"  • {prop_name} ({prop_type}) - {description}")
        
        if dry_run:
            print("\n🧪 DRY RUN: Would add the above properties to database")
            return True
            
        # Confirm update
        print(f"\n⚠️  This will update the database schema for: {database_id}")
        confirm = input("Continue with schema update? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Update cancelled")
            return False
        
        # Update database properties
        print("\n🚀 Updating database schema...")
        
        # Note: Notion API requires updating the entire properties object
        # We need to merge existing properties with new ones
        updated_properties = current_properties.copy()
        
        for prop_name, prop_config in properties_to_add.items():
            # Remove description field as it's not part of the API
            api_config = {k: v for k, v in prop_config.items() if k != 'description'}
            updated_properties[prop_name] = api_config
            
        # Update the database
        response = notion_client.client.databases.update(
            database_id=database_id,
            properties=updated_properties
        )
        
        if response:
            print(f"✅ Successfully added {len(properties_to_add)} new properties!")
            print("\n📋 New properties added:")
            for prop_name in properties_to_add.keys():
                print(f"  • {prop_name}")
            return True
        else:
            print("❌ Failed to update database schema")
            return False
            
    except Exception as e:
        logger.error(f"Schema update failed: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Update Notion database schema for multi-date support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_notion_schema.py --dry-run
  python update_notion_schema.py --database-id abc123def456
  python update_notion_schema.py
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Show what would be updated without making changes'
    )
    parser.add_argument(
        '--database-id', 
        help='Database ID to update (uses NOTION_DATABASE_ID from .env if not provided)'
    )
    
    args = parser.parse_args()
    
    # Get database ID
    database_id = args.database_id or os.environ.get("NOTION_DATABASE_ID")
    if not database_id:
        print("❌ Database ID required. Provide via --database-id or set NOTION_DATABASE_ID in .env")
        return 1
    
    print("🔧 Notion Database Schema Update for Multi-Date Support")
    print("=" * 60)
    print(f"Database ID: {database_id}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}")
    print("=" * 60)
    
    try:
        # Initialize Notion client
        notion_client = NotionClientWrapper()
        print("✅ Notion client initialized")
        
        # Update schema
        success = update_database_schema(notion_client, database_id, args.dry_run)
        
        if success:
            if not args.dry_run:
                print("\n🎉 Schema update completed successfully!")
                print("\n📝 Next steps:")
                print("1. Multi-date events will now use dedicated fields for series linking")
                print("2. Test the Smart Pipeline with multi-date events")
                print("3. Run the evaluation framework to validate functionality")
                print(f"4. Use 'python -m utils.notion_dev_utils database-info {database_id}' to verify changes")
            return 0
        else:
            print("❌ Schema update failed")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())