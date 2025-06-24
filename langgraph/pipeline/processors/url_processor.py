"""
Optimized URL processor for event extraction
"""

import logging
import time
from typing import Dict, Any, Optional
from langsmith.run_trees import RunTree
import langsmith
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)

class URLProcessor(BaseProcessor):
    """
    Optimized processor for URL-based event extraction
    
    Features:
    - Direct fetch + parse combination
    - Structured data extraction first
    - LLM fallback for complex cases
    - Async processing support (future)
    """
    
    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run)
        self.processor_type = "url"
    
    def process(self, classified_input: Dict[str, Any], source: str = "telegram", 
                user_id: Optional[str] = None, parent_run: Optional[RunTree] = None) -> Dict[str, Any]:
        """
        Process URL input and extract event data
        
        Args:
            classified_input: Output from SmartClassifier
            source: Source of the input
            user_id: Optional user identifier
            
        Returns:
            Dict containing extracted event data and metadata
        """
        start_time = time.time()
        
        try:
            # Create base result structure
            result = self._create_base_result(classified_input, source, user_id)
            
            # Extract URL from classified input
            url = classified_input.get("raw_input", "").strip()
            if not url:
                raise ValueError("No URL provided in classified input")
            
            # Step 1: Fetch URL content (with explicit child run)
            logger.debug(f"Fetching content from URL: {url}")
            content_result = self._fetch_url_content_traced(url, parent_run)
            
            if content_result.get("fetch_status") != "success":
                raise Exception(f"Failed to fetch URL content: {content_result.get('error', 'Unknown error')}")
            
            # Step 2: Parse content for event data (with explicit child run)
            logger.debug("Parsing URL content for event data")
            parsed_result = self._parse_url_content_traced(
                content_result.get("webpage_content", ""),
                content_result.get("webpage_title", "Untitled"),
                parent_run
            )
            
            # Step 3: Validate extracted data
            validation_result = self._validate_extracted_data(parsed_result)
            
            # Step 4: Save to Notion (or dry run) (with explicit child run)
            save_result = self._save_event_data_traced({
                **result,
                **parsed_result,
                **validation_result
            }, parent_run)
            
            # Combine all results
            final_result = {
                **result,
                **content_result,
                **parsed_result,
                **validation_result,
                **save_result,
                "processing_time": time.time() - start_time,
                "processor_type": self.processor_type
            }
            
            # Update statistics
            success = save_result.get("notion_save_status") == "success" or self.dry_run
            self._update_stats(success, final_result["processing_time"])
            
            logger.info(f"URL processing completed in {final_result['processing_time']:.2f}s")
            return final_result
            
        except Exception as e:
            error_result = self._create_base_result(classified_input, source, user_id)
            error_result.update({
                "error": str(e),
                "processing_status": "failed",
                "processing_time": time.time() - start_time,
                "processor_type": self.processor_type
            })
            
            self._update_stats(False, error_result["processing_time"])
            logger.error(f"URL processing failed: {e}")
            return error_result
    
    def _fetch_url_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch content from URL using existing tools
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Dict containing webpage content and metadata
        """
        try:
            # Use existing fetch_url_content tool
            from langgraph.agents.tools.fetch_url_tool import fetch_url_content
            return fetch_url_content(url)
            
        except Exception as e:
            logger.error(f"URL fetch failed: {e}")
            return {
                "error": str(e),
                "fetch_status": "failed",
                "webpage_content": "",
                "webpage_title": "Error"
            }
    
    def _parse_url_content(self, content: str, title: str = "Untitled") -> Dict[str, Any]:
        """
        Parse webpage content to extract event data
        
        Future optimizations:
        1. Try structured data extraction first (JSON-LD, microdata)
        2. Pattern-based extraction for known event sites
        3. LLM parsing as fallback
        
        Args:
            content: Webpage text content
            title: Webpage title
            
        Returns:
            Dict containing parsed event data
        """
        try:
            # For now, use existing parse_url_content tool
            # TODO: Implement smart parsing strategies
            from langgraph.agents.tools.parse_url_tool import parse_url_content
            
            # Call existing parser with content and title
            parse_input = {
                "webpage_content": content,
                "webpage_title": title
            }
            
            result = parse_url_content(parse_input)
            
            # Enhance with processing metadata
            result["parsing_method"] = "llm_fallback"  # Current method
            result["content_length"] = len(content)
            result["title_provided"] = bool(title and title != "Untitled")
            
            return result
            
        except Exception as e:
            logger.error(f"Content parsing failed: {e}")
            return {
                "error": str(e),
                "parsing_confidence": 0.0,
                "parsing_method": "failed",
                "event_title": "",
                "event_date": "",
                "event_location": "",
                "event_description": ""
            }
    
    def _save_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save event data to Notion or perform dry run
        
        Args:
            event_data: Complete event data to save
            
        Returns:
            Dict containing save results
        """
        try:
            # Extract only the fields needed for Notion save
            notion_data = {
                "input_type": event_data.get("input_type", "url"),
                "raw_input": event_data.get("raw_input", ""),
                "source": event_data.get("source", "pipeline"),
                "event_title": event_data.get("event_title", ""),
                "event_date": event_data.get("event_date", ""),
                "event_location": event_data.get("event_location", ""),
                "event_description": event_data.get("event_description", ""),
                "user_id": event_data.get("user_id")
            }
            
            if self.dry_run:
                # Use dry run save tool
                from langgraph.agents.tools.dry_run_save_notion_tool import dry_run_save_to_notion
                return dry_run_save_to_notion.invoke({"event_data": notion_data})
            else:
                # Use real save tool
                from langgraph.agents.tools.save_notion_tool import save_to_notion
                return save_to_notion.invoke({"event_data": notion_data})
                
        except Exception as e:
            logger.error(f"Save operation failed: {e}")
            return {
                "error": str(e),
                "notion_save_status": "failed",
                "notion_page_id": None,
                "notion_url": None
            }
    
    def _fetch_url_content_traced(self, url: str, parent_run: Optional[RunTree] = None) -> Dict[str, Any]:
        """Fetch URL content with explicit LangSmith child run"""
        if parent_run:
            fetch_run = parent_run.create_child(
                name="Fetch URL Content", 
                run_type="tool",
                inputs={"url": url}
            )
            fetch_run.post()
        
        try:
            result = self._fetch_url_content(url)
            
            if parent_run:
                fetch_run.end(outputs=result)
                fetch_run.patch()
            
            return result
        except Exception as e:
            if parent_run:
                fetch_run.end(error=str(e))
                fetch_run.patch()
            raise
    
    def _parse_url_content_traced(self, content: str, title: str, parent_run: Optional[RunTree] = None) -> Dict[str, Any]:
        """Parse URL content with explicit LangSmith child run"""
        if parent_run:
            parse_run = parent_run.create_child(
                name="Parse URL Content",
                run_type="tool", 
                inputs={"content_length": len(content), "title": title}
            )
            parse_run.post()
        
        try:
            result = self._parse_url_content(content, title)
            
            if parent_run:
                parse_run.end(outputs=result)
                parse_run.patch()
            
            return result
        except Exception as e:
            if parent_run:
                parse_run.end(error=str(e))
                parse_run.patch()
            raise
    
    def _save_event_data_traced(self, event_data: Dict[str, Any], parent_run: Optional[RunTree] = None) -> Dict[str, Any]:
        """Save event data with explicit LangSmith child run"""
        if parent_run:
            save_run = parent_run.create_child(
                name="Save to Notion" if not self.dry_run else "Dry Run Save to Notion",
                run_type="tool",
                inputs={"dry_run": self.dry_run, "has_event_data": bool(event_data.get("event_title"))}
            )
            save_run.post()
        
        try:
            result = self._save_event_data(event_data)
            
            if parent_run:
                save_run.end(outputs=result)
                save_run.patch()
            
            return result
        except Exception as e:
            if parent_run:
                save_run.end(error=str(e))
                save_run.patch()
            raise