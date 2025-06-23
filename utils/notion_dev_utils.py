"""
Notion Development Utilities

A command-line utility for common Notion API tasks during development.
Provides tools for token validation, database management, and data operations.

Usage:
    python -m utils.notion_dev_utils validate-token
    python -m utils.notion_dev_utils list-databases
    python -m utils.notion_dev_utils database-info <database_id>
    python -m utils.notion_dev_utils create-database
    python -m utils.notion_dev_utils query-pages <database_id>
    python -m utils.notion_dev_utils clean-database <database_id>
    python -m utils.notion_dev_utils export-database <database_id>
"""

import os
import json
import csv
import argparse
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from notion_client import APIResponseError, APIErrorCode
from .notion_client import NotionClientWrapper, create_events_database_schema

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class NotionDevUtils:
    """Development utilities for Notion API operations."""
    
    def __init__(self):
        """Initialize the utility with Notion client."""
        try:
            self.notion = NotionClientWrapper()
            logger.info("Notion client initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize Notion client: {e}")
            raise
    
    def validate_token(self) -> bool:
        """Validate the Notion token and check permissions."""
        print("🔍 Validating Notion token...")
        
        try:
            # Try to list databases to test permissions
            response = self.notion.client.search(
                filter={"property": "object", "value": "database"}
            )
            
            databases = response.get('results', [])
            print(f"✅ Token is valid! Found access to {len(databases)} database(s)")
            
            if len(databases) == 0:
                print("⚠️  No databases found. This could mean:")
                print("   - The integration hasn't been added to any pages")
                print("   - The integration doesn't have proper permissions")
            
            return True
            
        except APIResponseError as error:
            if error.code == APIErrorCode.Unauthorized:
                print("❌ Token is invalid or unauthorized")
                print("   Check your NOTION_TOKEN in the .env file")
            else:
                print(f"❌ API Error: {error}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """List all databases accessible to the integration."""
        print("📋 Listing accessible databases...")
        
        try:
            response = self.notion.client.search(
                filter={"property": "object", "value": "database"}
            )
            
            databases = response.get('results', [])
            
            if not databases:
                print("No databases found")
                return []
            
            print(f"\nFound {len(databases)} database(s):")
            print("-" * 80)
            
            for db in databases:
                title = "Untitled"
                if db.get('title') and len(db['title']) > 0:
                    title = db['title'][0]['plain_text']
                
                print(f"Title: {title}")
                print(f"ID: {db['id']}")
                print(f"URL: {db['url']}")
                print(f"Created: {db['created_time']}")
                print(f"Last edited: {db['last_edited_time']}")
                print("-" * 80)
            
            return databases
            
        except APIResponseError as error:
            print(f"❌ Failed to list databases: {error}")
            return []
    
    def get_database_info(self, database_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific database."""
        print(f"🔍 Getting database info for: {database_id}")
        
        try:
            database = self.notion.client.databases.retrieve(database_id=database_id)
            
            title = "Untitled"
            if database.get('title') and len(database['title']) > 0:
                title = database['title'][0]['plain_text']
            
            print(f"\n📊 Database: {title}")
            print(f"ID: {database['id']}")
            print(f"URL: {database['url']}")
            print(f"Created: {database['created_time']}")
            print(f"Last edited: {database['last_edited_time']}")
            
            # Show properties
            properties = database.get('properties', {})
            print(f"\n🏗️  Properties ({len(properties)}):")
            for prop_name, prop_config in properties.items():
                prop_type = prop_config.get('type', 'unknown')
                print(f"  • {prop_name} ({prop_type})")
                
                # Show select options if applicable
                if prop_type == 'select' and 'select' in prop_config:
                    options = prop_config['select'].get('options', [])
                    if options:
                        option_names = [opt['name'] for opt in options]
                        print(f"    Options: {', '.join(option_names)}")
            
            return database
            
        except APIResponseError as error:
            if error.code == APIErrorCode.ObjectNotFound:
                print("❌ Database not found or not accessible")
            else:
                print(f"❌ Failed to get database info: {error}")
            return None
    
    def create_database_interactive(self) -> Optional[str]:
        """Interactive database creation."""
        print("🏗️  Creating a new database...")
        
        # Get parent page ID
        parent_page_id = input("Enter the Page ID where you want to create the database: ").strip()
        if not parent_page_id:
            print("❌ Page ID is required")
            return None
        
        # Get database title
        title = input("Enter database title (default: 'SoBored Events'): ").strip()
        if not title:
            title = "SoBored Events"
        
        # Ask if they want to use the default schema
        use_default = input("Use default events schema? (y/n, default: y): ").strip().lower()
        if use_default in ['', 'y', 'yes']:
            schema = create_events_database_schema()
            print("Using default events schema")
        else:
            print("Custom schema creation not implemented yet. Using default schema.")
            schema = create_events_database_schema()
        
        try:
            database = self.notion.create_database(
                parent_page_id=parent_page_id,
                title=title,
                properties=schema
            )
            
            if database:
                database_id = database['id']
                print(f"✅ Database created successfully!")
                print(f"Database ID: {database_id}")
                print(f"URL: {database['url']}")
                print(f"\n📝 Add this to your .env file:")
                print(f"NOTION_DATABASE_ID={database_id}")
                return database_id
            else:
                print("❌ Failed to create database")
                return None
                
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return None
    
    def query_pages(self, database_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Query pages in a database."""
        print(f"📄 Querying pages in database: {database_id}")
        
        try:
            response = self.notion.client.databases.query(
                database_id=database_id,
                page_size=limit
            )
            
            pages = response.get('results', [])
            
            if not pages:
                print("No pages found in database")
                return []
            
            print(f"\nFound {len(pages)} page(s):")
            print("-" * 80)
            
            for page in pages:
                # Try to get title from properties
                title = "Untitled"
                properties = page.get('properties', {})
                
                # Look for title property
                for prop_name, prop_value in properties.items():
                    if prop_value.get('type') == 'title':
                        title_array = prop_value.get('title', [])
                        if title_array:
                            title = title_array[0].get('plain_text', 'Untitled')
                        break
                
                print(f"Title: {title}")
                print(f"ID: {page['id']}")
                print(f"URL: {page['url']}")
                print(f"Created: {page['created_time']}")
                print("-" * 80)
            
            return pages
            
        except APIResponseError as error:
            print(f"❌ Failed to query pages: {error}")
            return []
    
    def list_pages(self, database_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List pages from a specific database or search all accessible pages."""
        if database_id:
            print(f"📄 Listing pages from database: {database_id}")
            # Use the existing query_pages method for database-specific queries
            return self.query_pages(database_id, limit)
        else:
            print("📄 Searching all accessible pages...")
            
            try:
                response = self.notion.client.search(
                    filter={"property": "object", "value": "page"},
                    page_size=limit
                )
                
                pages = response.get('results', [])
                
                if not pages:
                    print("No pages found")
                    return []
                
                print(f"\nFound {len(pages)} page(s) across all accessible workspaces:")
                print("-" * 80)
                
                for page in pages:
                    # Try to get title from properties or title field
                    title = "Untitled"
                    
                    # Check if it's a database page with properties
                    if page.get('properties'):
                        properties = page.get('properties', {})
                        for prop_name, prop_value in properties.items():
                            if prop_value.get('type') == 'title':
                                title_array = prop_value.get('title', [])
                                if title_array:
                                    title = title_array[0].get('plain_text', 'Untitled')
                                break
                    # Check if it's a regular page with title
                    elif page.get('properties') is None and page.get('title'):
                        title_array = page.get('title', [])
                        if title_array:
                            title = title_array[0].get('plain_text', 'Untitled')
                    
                    # Get parent info
                    parent = page.get('parent', {})
                    parent_type = parent.get('type', 'unknown')
                    parent_info = f"{parent_type}"
                    if parent_type == 'database_id':
                        parent_info = f"database ({parent.get('database_id', '')[:8]}...)"
                    elif parent_type == 'page_id':
                        parent_info = f"page ({parent.get('page_id', '')[:8]}...)"
                    elif parent_type == 'workspace':
                        parent_info = "workspace"
                    
                    print(f"Title: {title}")
                    print(f"ID: {page['id']}")
                    print(f"Parent: {parent_info}")
                    print(f"URL: {page['url']}")
                    print(f"Created: {page['created_time']}")
                    print("-" * 80)
                
                return pages
                
            except APIResponseError as error:
                print(f"❌ Failed to list pages: {error}")
                return []
    
    def clean_database(self, database_id: str, dry_run: bool = False) -> bool:
        """Remove all pages from a database."""
        if dry_run:
            print(f"🧪 DRY RUN: Would clean database: {database_id}")
        else:
            print(f"🗑️  Cleaning database: {database_id}")
        
        # Get all pages first
        try:
            response = self.notion.client.databases.query(database_id=database_id)
            pages = response.get('results', [])
            
            if not pages:
                print("Database is already empty")
                return True
            
            print(f"Found {len(pages)} page(s) to delete")
            
            if not dry_run:
                confirm = input(f"Are you sure you want to delete {len(pages)} pages? (y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    print("Operation cancelled")
                    return False
            
            # Delete pages
            deleted_count = 0
            for page in pages:
                if dry_run:
                    print(f"Would delete: {page['id']}")
                    deleted_count += 1
                else:
                    try:
                        self.notion.client.pages.update(
                            page_id=page['id'],
                            archived=True
                        )
                        deleted_count += 1
                        print(f"Deleted page {deleted_count}/{len(pages)}")
                    except APIResponseError as error:
                        print(f"Failed to delete page {page['id']}: {error}")
            
            if dry_run:
                print(f"DRY RUN: Would delete {deleted_count} pages")
            else:
                print(f"✅ Successfully deleted {deleted_count} pages")
            
            return True
            
        except APIResponseError as error:
            print(f"❌ Failed to clean database: {error}")
            return False
    
    def export_database(self, database_id: str, format: str = 'json', output_file: Optional[str] = None) -> bool:
        """Export database contents to JSON or CSV."""
        print(f"📤 Exporting database: {database_id}")
        
        try:
            # Get all pages
            response = self.notion.client.databases.query(database_id=database_id)
            pages = response.get('results', [])
            
            if not pages:
                print("No pages to export")
                return True
            
            # Prepare output filename
            if not output_file:
                output_file = f"database_export_{database_id[:8]}.{format}"
            
            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(pages, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                if not pages:
                    print("No data to export")
                    return True
                
                # Extract property names from first page
                first_page = pages[0]
                properties = first_page.get('properties', {})
                fieldnames = ['id', 'url', 'created_time'] + list(properties.keys())
                
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for page in pages:
                        row = {
                            'id': page['id'],
                            'url': page['url'],
                            'created_time': page['created_time']
                        }
                        
                        # Extract property values
                        for prop_name, prop_value in page.get('properties', {}).items():
                            prop_type = prop_value.get('type')
                            
                            if prop_type == 'title':
                                title_array = prop_value.get('title', [])
                                row[prop_name] = title_array[0].get('plain_text', '') if title_array else ''
                            elif prop_type == 'rich_text':
                                text_array = prop_value.get('rich_text', [])
                                row[prop_name] = text_array[0].get('plain_text', '') if text_array else ''
                            elif prop_type == 'select':
                                select_obj = prop_value.get('select')
                                row[prop_name] = select_obj.get('name', '') if select_obj else ''
                            elif prop_type == 'date':
                                date_obj = prop_value.get('date')
                                row[prop_name] = date_obj.get('start', '') if date_obj else ''
                            elif prop_type == 'url':
                                row[prop_name] = prop_value.get('url', '')
                            else:
                                row[prop_name] = str(prop_value)
                        
                        writer.writerow(row)
            
            else:
                print(f"❌ Unsupported format: {format}")
                return False
            
            print(f"✅ Exported {len(pages)} pages to {output_file}")
            return True
            
        except APIResponseError as error:
            print(f"❌ Failed to export database: {error}")
            return False
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Notion Development Utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m utils.notion_dev_utils validate-token
  python -m utils.notion_dev_utils list-databases
  python -m utils.notion_dev_utils database-info abc123
  python -m utils.notion_dev_utils create-database
  python -m utils.notion_dev_utils query-pages abc123 --limit 5
  python -m utils.notion_dev_utils list-pages --database-id abc123 --limit 5
  python -m utils.notion_dev_utils list-pages --limit 20
  python -m utils.notion_dev_utils clean-database abc123 --dry-run
  python -m utils.notion_dev_utils export-database abc123 --format csv
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate token command
    subparsers.add_parser('validate-token', help='Validate Notion token and permissions')
    
    # List databases command
    subparsers.add_parser('list-databases', help='List all accessible databases')
    
    # Database info command
    db_info_parser = subparsers.add_parser('database-info', help='Get detailed database information')
    db_info_parser.add_argument('database_id', help='Database ID')
    
    # Create database command
    subparsers.add_parser('create-database', help='Create a new database interactively')
    
    # Query pages command
    query_parser = subparsers.add_parser('query-pages', help='Query pages in a database')
    query_parser.add_argument('database_id', help='Database ID')
    query_parser.add_argument('--limit', type=int, default=10, help='Maximum number of pages to return')
    
    # List pages command
    list_parser = subparsers.add_parser('list-pages', help='List pages from a database or search all accessible pages')
    list_parser.add_argument('--database-id', help='Database ID (optional - if not provided, searches all accessible pages)')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum number of pages to return')
    
    # Clean database command
    clean_parser = subparsers.add_parser('clean-database', help='Remove all pages from a database')
    clean_parser.add_argument('database_id', help='Database ID')
    clean_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    
    # Export database command
    export_parser = subparsers.add_parser('export-database', help='Export database contents')
    export_parser.add_argument('database_id', help='Database ID')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    export_parser.add_argument('--output', help='Output filename')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        utils = NotionDevUtils()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("Make sure NOTION_TOKEN is set in your .env file")
        return
    
    # Execute commands
    if args.command == 'validate-token':
        utils.validate_token()
    
    elif args.command == 'list-databases':
        utils.list_databases()
    
    elif args.command == 'database-info':
        utils.get_database_info(args.database_id)
    
    elif args.command == 'create-database':
        utils.create_database_interactive()
    
    elif args.command == 'query-pages':
        utils.query_pages(args.database_id, args.limit)
    
    elif args.command == 'list-pages':
        utils.list_pages(getattr(args, 'database_id', None), args.limit)
    
    elif args.command == 'clean-database':
        utils.clean_database(args.database_id, args.dry_run)
    
    elif args.command == 'export-database':
        utils.export_database(args.database_id, args.format, args.output)


if __name__ == '__main__':
    main()