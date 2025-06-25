"""
Unified NotionSaver class that handles both real and dry-run Notion saves.

This eliminates the duplication between save_to_notion and dry_run_save_to_notion
by using a composition pattern with configurable behavior.
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime
import pytz


class NotionSaver:
    """
    Unified class for saving events to Notion with configurable dry-run mode.
    
    This class consolidates the logic from both save_to_notion and dry_run_save_to_notion
    tools, eliminating code duplication and providing a single source of truth.
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize the NotionSaver.
        
        Args:
            dry_run: If True, performs mock saves without actual Notion API calls
        """
        self.dry_run = dry_run
        if self.dry_run:
            print("[NOTION-SAVER] *** DRY-RUN MODE - NO ACTUAL NOTION API CALLS WILL BE MADE ***")
        
    def save(self, event_data: Union[dict, str]) -> Dict[str, Any]:
        """
        Save event data to Notion (real or mock based on dry_run mode).
        
        Args:
            event_data: Dictionary containing event information with fields:
                       input_type, raw_input, source, event_title, event_date, 
                       event_location, event_description, user_id (optional)
            
        Returns:
            Dict containing save status and Notion page details
        """
        mode = "DRY-RUN" if self.dry_run else "SAVE"
        print(f"[{mode}] Event data type: {type(event_data)}")
        print(f"[{mode}] Event data: {event_data}")
        
        try:
            # Parse and validate event data
            data = self._parse_event_data(event_data)
            if "error" in data:
                return data
                
            # Extract fields
            input_type = data.get("input_type", "unknown")
            raw_input = data.get("raw_input", "")
            source = data.get("source", "unknown")
            event_title = data.get("event_title")
            event_date = data.get("event_date")
            event_location = data.get("event_location")
            event_description = data.get("event_description")
            user_id = data.get("user_id")
            
            # Skip saving if input_type is unknown or error
            if input_type in ['unknown', 'error']:
                return {
                    "notion_save_status": "dry_run_skipped" if self.dry_run else "skipped",
                    "reason": f"{'Would skip' if self.dry_run else 'Skipping'} save for input_type: {input_type}",
                    "dry_run": self.dry_run
                }
            
            # Handle multi-instance events (multiple dates)
            if event_date and ',' in str(event_date):
                return self._save_multi_instance_event(
                    input_type, raw_input, source, event_title,
                    event_date, event_location, event_description, user_id
                )
            
            # Handle single instance event
            return self._save_single_instance_event(
                input_type, raw_input, source, event_title,
                event_date, event_location, event_description, user_id
            )
            
        except Exception as e:
            mode = "DRY-RUN" if self.dry_run else "SAVE"
            print(f"[{mode}] Error processing event_data: {e}")
            return {
                "notion_save_status": "dry_run_failed" if self.dry_run else "failed",
                "notion_error": f"Error processing event_data: {str(e)}",
                "dry_run": self.dry_run
            }
    
    def _parse_event_data(self, event_data: Union[dict, str]) -> Dict[str, Any]:
        """Parse and validate event data input."""
        try:
            # Handle both dict and string inputs for backward compatibility
            if isinstance(event_data, str):
                # Handle case where agent passes a string that looks like Python dict representation
                try:
                    # First try to parse as JSON
                    cleaned_event_data = event_data.replace('None', 'null').replace("'", '"')
                    data = json.loads(cleaned_event_data)
                    print(f"[PARSE] Parsed JSON string to dict: {data}")
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to evaluate as Python literal
                    try:
                        import ast
                        data = ast.literal_eval(event_data)
                        print(f"[PARSE] Parsed Python literal to dict: {data}")
                    except (ValueError, SyntaxError):
                        print(f"[PARSE] Failed to parse as JSON or Python literal: {event_data[:200]}...")
                        return {
                            "error": True,
                            "notion_save_status": "dry_run_failed" if self.dry_run else "failed",
                            "notion_error": f"Could not parse event_data string as dict or JSON"
                        }
            elif isinstance(event_data, dict):
                data = event_data
                print(f"[PARSE] Using dict input directly: {data}")
            else:
                return {
                    "error": True,
                    "notion_save_status": "dry_run_failed" if self.dry_run else "failed",
                    "notion_error": f"Invalid event_data type: {type(event_data)}. Expected dict or str."
                }
            
            return data
            
        except Exception as e:
            return {
                "error": True,
                "notion_save_status": "dry_run_failed" if self.dry_run else "failed",
                "notion_error": f"Error parsing event_data: {str(e)}"
            }
    
    def _save_single_instance_event(
        self,
        input_type: str,
        raw_input: str,
        source: str,
        event_title: Optional[str],
        event_date: Optional[str],
        event_location: Optional[str],
        event_description: Optional[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Save a single instance event."""
        if self.dry_run:
            return self._mock_single_save(
                input_type, raw_input, source, event_title,
                event_date, event_location, event_description, user_id
            )
        else:
            return self._real_single_save(
                input_type, raw_input, source, event_title,
                event_date, event_location, event_description, user_id
            )
    
    def _save_multi_instance_event(
        self,
        input_type: str,
        raw_input: str,
        source: str,
        event_title: Optional[str],
        event_date: str,
        event_location: Optional[str],
        event_description: Optional[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Save multi-instance event as separate records with series linking."""
        if self.dry_run:
            return self._mock_multi_save(
                input_type, raw_input, source, event_title,
                event_date, event_location, event_description, user_id
            )
        else:
            return self._real_multi_save(
                input_type, raw_input, source, event_title,
                event_date, event_location, event_description, user_id
            )
    
    def _real_single_save(
        self,
        input_type: str,
        raw_input: str,
        source: str,
        event_title: Optional[str],
        event_date: Optional[str],
        event_location: Optional[str],
        event_description: Optional[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Perform real save to Notion for single instance."""
        # Check database configuration
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if not database_id:
            return {
                "notion_save_status": "failed",
                "notion_error": "Database ID not configured"
            }
        
        try:
            # Initialize Notion client
            from utils.notion_client import get_notion_client
            notion_client = get_notion_client()
            
            # Build page properties
            properties = self._build_notion_properties(
                input_type, raw_input, source, event_title,
                event_date, event_location, event_description, user_id
            )
            
            # Create page in Notion database
            page = notion_client.create_page(database_id, properties)
            
            if page:
                # Construct Notion URL
                page_id_clean = page['id'].replace('-', '')
                notion_url = f"https://www.notion.so/{page_id_clean}"
                
                return {
                    "notion_save_status": "success",
                    "notion_page_id": page['id'],
                    "notion_url": notion_url
                }
            else:
                return {
                    "notion_save_status": "failed",
                    "notion_error": "Failed to create page in Notion"
                }
                
        except Exception as e:
            return {
                "notion_save_status": "failed",
                "notion_error": str(e)
            }
    
    def _mock_single_save(
        self,
        input_type: str,
        raw_input: str,
        source: str,
        event_title: Optional[str],
        event_date: Optional[str],
        event_location: Optional[str],
        event_description: Optional[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Perform mock save for single instance (dry-run mode)."""
        # Check database configuration (mock)
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if not database_id:
            return {
                "notion_save_status": "dry_run_failed",
                "notion_error": "Database ID not configured (would fail in real save)",
                "dry_run": True
            }
        
        # Build the properties that would be sent to Notion
        properties = self._build_notion_properties(
            input_type, raw_input, source, event_title,
            event_date, event_location, event_description, user_id
        )
        
        # Generate what the Notion page would look like
        mock_page_id = "dry-run-page-id-12345"
        page_id_clean = mock_page_id.replace('-', '')
        notion_url = f"https://www.notion.so/{page_id_clean}"
        
        result = {
            "notion_save_status": "dry_run_success",
            "notion_page_id": mock_page_id,
            "notion_url": notion_url,
            "dry_run": True,
            "would_save_properties": properties,
            "database_id": database_id,
            "event_data": {
                "input_type": input_type,
                "raw_input": raw_input,
                "source": source,
                "event_title": event_title,
                "event_date": event_date,
                "event_location": event_location,
                "event_description": event_description,
                "user_id": user_id
            }
        }
        
        print("[DRY-RUN SAVE] *** COMPLETED DRY-RUN - NO DATA WAS ACTUALLY SAVED TO NOTION ***")
        return result
    
    def _real_multi_save(
        self,
        input_type: str,
        raw_input: str,
        source: str,
        event_title: Optional[str],
        event_date: str,
        event_location: Optional[str],
        event_description: Optional[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Perform real multi-instance save to Notion."""
        try:
            # Parse multiple dates
            dates = [d.strip() for d in event_date.split(',')]
            
            # Generate series ID
            series_content = f"{event_title}_{event_location}_{user_id}_{int(time.time())}"
            series_id = hashlib.md5(series_content.encode()).hexdigest()[:8]
            
            print(f"[SAVE] Creating multi-instance event: {len(dates)} sessions")
            print(f"[SAVE] Series ID: {series_id}")
            
            # Get database ID
            database_id = os.environ.get("NOTION_DATABASE_ID")
            if not database_id:
                return {
                    "notion_save_status": "failed",
                    "notion_error": "Database ID not configured"
                }
            
            # Initialize Notion client
            from utils.notion_client import get_notion_client
            notion_client = get_notion_client()
            
            created_pages = []
            series_urls = []
            
            # Create a record for each date
            for i, date in enumerate(dates):
                # Format date for Notion (handle various formats)
                formatted_date = self._format_date_for_notion(date)
                
                # Create session title
                session_title = f"{event_title} (Session {i+1} of {len(dates)})"
                
                # Build properties for this instance with series metadata
                properties = self._build_notion_properties(
                    input_type=input_type,
                    raw_input=raw_input,
                    source=source,
                    event_title=session_title,
                    event_date=formatted_date,
                    event_location=event_location,
                    event_description=event_description,
                    user_id=user_id,
                    series_id=series_id,
                    session_number=i + 1,
                    total_sessions=len(dates)
                )
                
                # Create the page
                page = notion_client.create_page(database_id, properties)
                
                if page:
                    page_id_clean = page['id'].replace('-', '')
                    notion_url = f"https://www.notion.so/{page_id_clean}"
                    created_pages.append(page['id'])
                    series_urls.append(notion_url)
                    print(f"[SAVE] Created session {i+1}: {page['id']}")
                else:
                    print(f"[SAVE] Failed to create session {i+1}")
            
            if created_pages:
                return {
                    "notion_save_status": "success",
                    "notion_page_id": created_pages[0],  # Return first page ID
                    "notion_url": series_urls[0],  # Return first URL
                    "series_id": series_id,
                    "total_sessions": len(dates),
                    "created_sessions": len(created_pages),
                    "all_page_ids": created_pages,
                    "all_urls": series_urls,
                    "event_title": f"{event_title} (Series of {len(dates)})"
                }
            else:
                return {
                    "notion_save_status": "failed",
                    "notion_error": "Failed to create any session records"
                }
                
        except Exception as e:
            print(f"[SAVE] Multi-instance save error: {e}")
            return {
                "notion_save_status": "failed",
                "notion_error": f"Multi-instance save failed: {str(e)}"
            }
    
    def _mock_multi_save(
        self,
        input_type: str,
        raw_input: str,
        source: str,
        event_title: Optional[str],
        event_date: str,
        event_location: Optional[str],
        event_description: Optional[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Perform mock multi-instance save (dry-run mode)."""
        try:
            # Parse multiple dates
            dates = [d.strip() for d in event_date.split(',')]
            print(f"[DRY-RUN] Would create {len(dates)} separate records for multi-instance event")
            print(f"[DRY-RUN] Sessions: {', '.join(dates)}")
            
            # Generate series ID (same logic as real tool)
            series_content = f"{event_title}_{event_location}_{user_id}_{int(time.time())}"
            series_id = hashlib.md5(series_content.encode()).hexdigest()[:8]
            
            print(f"[DRY-RUN] Series ID: {series_id}")
            
            # Create mock data for each session
            created_pages = []
            series_urls = []
            session_details = []
            
            for i, date in enumerate(dates):
                # Create session title (same logic as real tool)
                session_title = f"{event_title} (Session {i+1} of {len(dates)})"
                mock_page_id = f"dry-run-session-{i+1}-{series_id}"
                page_id_clean = mock_page_id.replace('-', '')
                notion_url = f"https://www.notion.so/{page_id_clean}"
                
                created_pages.append(mock_page_id)
                series_urls.append(notion_url)
                
                # Build properties for this session with series metadata
                session_properties = self._build_notion_properties(
                    input_type=input_type,
                    raw_input=raw_input,
                    source=source,
                    event_title=session_title,
                    event_date=date,
                    event_location=event_location,
                    event_description=event_description,
                    user_id=user_id,
                    series_id=series_id,
                    session_number=i + 1,
                    total_sessions=len(dates)
                )
                
                session_details.append({
                    "session_number": i + 1,
                    "session_title": session_title,
                    "session_date": date,
                    "page_id": mock_page_id,
                    "notion_url": notion_url,
                    "properties": session_properties
                })
                
                print(f"[DRY-RUN] Session {i+1}: {session_title} at {date}")
            
            # Return comprehensive session linking data (matching real tool format)
            return {
                "notion_save_status": "success",
                "notion_page_id": created_pages[0],  # Return first page ID
                "notion_url": series_urls[0],  # Return first URL
                "series_id": series_id,
                "total_sessions": len(dates),
                "created_sessions": len(created_pages),
                "all_page_ids": created_pages,
                "all_urls": series_urls,
                "event_title": f"{event_title} (Series of {len(dates)})",
                "dry_run": True,
                "session_details": session_details,
                "dry_run_note": f"Would create {len(dates)} separate Notion records with series linking"
            }
            
        except Exception as e:
            print(f"[DRY-RUN] Multi-instance save error: {e}")
            return {
                "notion_save_status": "dry_run_failed",
                "notion_error": f"Multi-instance dry-run failed: {str(e)}",
                "dry_run": True
            }
    
    def _build_notion_properties(
        self,
        input_type: str,
        raw_input: str, 
        source: str,
        event_title: Optional[str],
        event_date: Optional[str],
        event_location: Optional[str],
        event_description: Optional[str],
        user_id: Optional[str] = None,
        series_id: Optional[str] = None,
        session_number: Optional[int] = None,
        total_sessions: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build Notion page properties from event data.
        
        Args:
            input_type: Type of input
            raw_input: Original raw input content
            source: Source of the input
            event_title: Event title
            event_date: Event date
            event_location: Event location
            event_description: Event description
            user_id: User ID from Telegram or other source
            series_id: Series ID for multi-instance events
            session_number: Session number (1, 2, 3, etc.)
            total_sessions: Total sessions in the series
            
        Returns:
            Dictionary of Notion page properties
        """
        properties = {}
        
        # Title (required)
        title_text = event_title or self._generate_fallback_title(input_type, raw_input, source)
        properties["Title"] = {
            "title": [
                {
                    "type": "text",
                    "text": {"content": title_text}
                }
            ]
        }
        
        # Date/Time
        if event_date:
            properties["Date/Time"] = {
                "date": {"start": event_date}
            }
        
        # Location
        if event_location:
            properties["Location"] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": event_location}
                    }
                ]
            }
        
        # Description
        description_text = event_description or raw_input
        if description_text:
            properties["Description"] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": description_text}
                    }
                ]
            }
        
        # Source
        if source:
            properties["Source"] = {
                "select": {"name": source}
            }
        
        # URL (if input is a URL)
        if input_type == 'url' and self._is_valid_url(raw_input):
            properties["URL"] = {
                "url": raw_input
            }
        
        # Classification
        if input_type:
            properties["Classification"] = {
                "select": {"name": input_type}
            }
        
        # Status (default to 'new')
        properties["Status"] = {
            "select": {"name": "new"}
        }
        
        # UserId (from Telegram or other source)
        if user_id:
            properties["UserId"] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": str(user_id)}
                    }
                ]
            }
        
        # Added timestamp (current datetime when record is created)
        est = pytz.timezone('US/Eastern')
        current_time = datetime.now(est).isoformat()
        properties["Added"] = {
            "date": {"start": current_time}
        }
        
        # Series metadata (for multi-instance events)
        if series_id:
            properties["Series ID"] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": series_id}
                    }
                ]
            }
        
        if session_number is not None:
            properties["Session Number"] = {
                "number": session_number
            }
        
        if total_sessions is not None:
            properties["Total Sessions"] = {
                "number": total_sessions
            }
        
        return properties
    
    def _format_date_for_notion(self, date_str: str) -> str:
        """
        Format date string for Notion's ISO 8601 requirement.
        
        Args:
            date_str: Date string to format
            
        Returns:
            ISO 8601 formatted date string
        """
        date_str = date_str.strip()
        
        # Handle "YYYY-MM-DD HH:MM" format
        if len(date_str) == 16 and ' ' in date_str:
            return date_str.replace(' ', 'T') + ':00'
        
        # Handle "YYYY-MM-DD" format
        if len(date_str) == 10 and date_str.count('-') == 2:
            return date_str + 'T00:00:00'
        
        # Return as-is for other formats (hopefully already ISO 8601)
        return date_str
    
    def _generate_fallback_title(self, input_type: str, raw_input: str, source: str) -> str:
        """
        Generate a fallback title when no event title is available.
        
        Args:
            input_type: Type of input
            raw_input: Original raw input content
            source: Source of the input
            
        Returns:
            Generated title string
        """
        if input_type == 'url':
            return f"URL: {raw_input[:50]}..."
        elif input_type == 'image':
            return f"Image from {source}"
        elif input_type == 'text':
            # Use first 50 characters of text as title
            return raw_input[:50] + ("..." if len(raw_input) > 50 else "")
        else:
            return f"{input_type.capitalize()} from {source}"
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a string is a valid URL.
        
        Args:
            url: String to validate
            
        Returns:
            True if valid URL, False otherwise
        """
        try:
            return url.startswith(('http://', 'https://'))
        except:
            return False