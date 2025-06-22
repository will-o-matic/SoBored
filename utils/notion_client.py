"""
Notion client initialization and configuration.
"""
import os
import logging
from notion_client import Client, APIResponseError, APIErrorCode
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NotionClientWrapper:
    """Wrapper for Notion client with error handling and utilities."""
    
    def __init__(self, auth_token: Optional[str] = None):
        """Initialize Notion client with authentication token."""
        self.token = auth_token or os.environ.get("NOTION_TOKEN")
        if not self.token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        
        self.client = Client(
            auth=self.token,
            log_level=logging.INFO
        )
        logger.info("Notion client initialized successfully")
    
    def create_database(self, parent_page_id: str, title: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new database in Notion."""
        try:
            database = self.client.databases.create(
                parent={
                    "type": "page_id",
                    "page_id": parent_page_id
                },
                title=[
                    {
                        "type": "text",
                        "text": {"content": title}
                    }
                ],
                properties=properties
            )
            logger.info(f"Database created successfully: {database['id']}")
            return database
        except APIResponseError as error:
            logger.error(f"Failed to create database: {error}")
            return None
    
    def create_page(self, database_id: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new page in a database."""
        try:
            page = self.client.pages.create(
                parent={
                    "type": "database_id",
                    "database_id": database_id
                },
                properties=properties
            )
            logger.info(f"Page created successfully: {page['id']}")
            return page
        except APIResponseError as error:
            if error.code == APIErrorCode.ObjectNotFound:
                logger.error(f"Database not found: {database_id}")
            elif error.code == APIErrorCode.Unauthorized:
                logger.error("Unauthorized: Check integration permissions")
            else:
                logger.error(f"Failed to create page: {error}")
            return None
    
    def query_database(self, database_id: str, filter_criteria: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Query a database with optional filters."""
        try:
            query_params = {"database_id": database_id}
            if filter_criteria:
                query_params["filter"] = filter_criteria
            
            results = self.client.databases.query(**query_params)
            logger.info(f"Database query successful: {len(results['results'])} results")
            return results
        except APIResponseError as error:
            logger.error(f"Failed to query database: {error}")
            return None
    
    def get_database(self, database_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve database information."""
        try:
            database = self.client.databases.retrieve(database_id=database_id)
            logger.info(f"Database retrieved successfully: {database['id']}")
            return database
        except APIResponseError as error:
            logger.error(f"Failed to retrieve database: {error}")
            return None


def get_notion_client() -> NotionClientWrapper:
    """Get a configured Notion client instance."""
    return NotionClientWrapper()


def create_events_database_schema() -> Dict[str, Any]:
    """Define the schema for the events database."""
    return {
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
                    {"name": "instagram", "color": "pink"}
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
        }
    }