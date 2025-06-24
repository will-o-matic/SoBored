"""
Text processor for direct event extraction from text input
"""

import logging
import time
from typing import Dict, Any, Optional
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)

class TextProcessor(BaseProcessor):
    """
    Processor for direct text-based event extraction
    
    Features:
    - Direct NLP processing (no agent overhead)
    - Pattern-based extraction for simple cases
    - LLM extraction for complex text
    """
    
    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run)
        self.processor_type = "text"
    
    def process(self, classified_input: Dict[str, Any], source: str = "telegram", 
                user_id: Optional[str] = None, parent_run=None) -> Dict[str, Any]:
        """
        Process text input and extract event data
        
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
            
            # Extract text from classified input
            text = classified_input.get("raw_input", "").strip()
            if not text:
                raise ValueError("No text provided in classified input")
            
            # Step 1: Parse text for event data
            logger.debug("Parsing text for event data")
            parsed_result = self._parse_text_content(text)
            
            # Step 2: Validate extracted data
            validation_result = self._validate_extracted_data(parsed_result)
            
            # Step 3: Save to Notion (or dry run)
            save_result = self._save_event_data({
                **result,
                **parsed_result,
                **validation_result
            })
            
            # Combine all results
            final_result = {
                **result,
                **parsed_result,
                **validation_result,
                **save_result,
                "processing_time": time.time() - start_time,
                "processor_type": self.processor_type
            }
            
            # Update statistics
            success = save_result.get("notion_save_status") == "success" or self.dry_run
            self._update_stats(success, final_result["processing_time"])
            
            logger.info(f"Text processing completed in {final_result['processing_time']:.2f}s")
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
            logger.error(f"Text processing failed: {e}")
            return error_result
    
    def _parse_text_content(self, text: str) -> Dict[str, Any]:
        """
        Parse text content to extract event data
        
        Future optimizations:
        1. Pattern-based extraction for simple formats
        2. NLP-based extraction for structured text
        3. LLM parsing for complex/ambiguous text
        
        Args:
            text: Raw text content
            
        Returns:
            Dict containing parsed event data
        """
        try:
            # For now, use Claude API directly for text parsing
            # TODO: Implement pattern-based extraction for simple cases
            
            result = self._llm_parse_text(text)
            
            # Enhance with processing metadata
            result["parsing_method"] = "llm_direct"
            result["text_length"] = len(text)
            result["word_count"] = len(text.split())
            
            return result
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return {
                "error": str(e),
                "parsing_confidence": 0.0,
                "parsing_method": "failed",
                "event_title": "",
                "event_date": "",
                "event_location": "",
                "event_description": text  # Fallback to original text
            }
    
    def _llm_parse_text(self, text: str) -> Dict[str, Any]:
        """
        Use LLM to parse text content for event data
        
        Args:
            text: Text content to parse
            
        Returns:
            Dict containing extracted event information
        """
        try:
            # Import and use Claude API for text parsing
            from anthropic import Anthropic
            import os
            
            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            # Get current date for context
            from datetime import datetime
            import pytz
            
            est = pytz.timezone('US/Eastern')
            current_date = datetime.now(est)
            current_date_str = current_date.strftime("%Y-%m-%d")
            current_year = current_date.year
            
            prompt = f"""
            Extract event information from the following text. Return a JSON object with these fields:
            - event_title: The name/title of the event
            - event_date: Date and time (in YYYY-MM-DD HH:MM format if possible)
            - event_location: Venue/location of the event
            - event_description: Brief description of the event
            - parsing_confidence: Confidence score between 0.0 and 1.0
            
            IMPORTANT DATE CONTEXT:
            - Current date: {current_date_str}
            - Current year: {current_year}
            - When parsing dates without explicit years (like "June 25th"), assume the current year {current_year}
            - For past dates in the current year or dates that seem to refer to future events, use {current_year}
            
            If any information is not available, use empty string for that field.
            
            Text to parse:
            {text}
            
            JSON:
            """
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response.content[0].text)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract manually
                return self._extract_from_response(response.content[0].text)
                
        except Exception as e:
            logger.error(f"LLM text parsing failed: {e}")
            # Fallback to simple extraction
            return self._simple_text_extraction(text)
    
    def _extract_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract event data from LLM response if JSON parsing fails
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Dict containing extracted data
        """
        # Simple fallback extraction
        lines = response_text.split('\n')
        result = {
            "event_title": "",
            "event_date": "",
            "event_location": "",
            "event_description": "",
            "parsing_confidence": 0.5
        }
        
        for line in lines:
            line = line.strip()
            if 'title' in line.lower():
                result["event_title"] = line.split(':', 1)[-1].strip().strip('"')
            elif 'date' in line.lower():
                result["event_date"] = line.split(':', 1)[-1].strip().strip('"')
            elif 'location' in line.lower():
                result["event_location"] = line.split(':', 1)[-1].strip().strip('"')
            elif 'description' in line.lower():
                result["event_description"] = line.split(':', 1)[-1].strip().strip('"')
        
        return result
    
    def _simple_text_extraction(self, text: str) -> Dict[str, Any]:
        """
        Simple pattern-based extraction as ultimate fallback
        
        Args:
            text: Text to extract from
            
        Returns:
            Dict containing basic extracted data
        """
        # Very basic extraction using patterns from classifier
        from langgraph.pipeline.classifiers.patterns import TEXT_PATTERNS
        
        result = {
            "event_title": "",
            "event_date": "",
            "event_location": "",
            "event_description": text,
            "parsing_confidence": 0.3,
            "parsing_method": "pattern_fallback"
        }
        
        # Try to extract date
        date_match = TEXT_PATTERNS["date_time"].search(text)
        if date_match:
            result["event_date"] = date_match.group()
            
        # Try to extract location indicators
        location_match = TEXT_PATTERNS["location_indicators"].search(text)
        if location_match:
            # Find text around location indicator
            location_context = text[max(0, location_match.start()-20):location_match.end()+20]
            result["event_location"] = location_context.strip()
        
        # Use first sentence as title if available
        sentences = text.split('.')
        if sentences:
            result["event_title"] = sentences[0].strip()[:100]  # Limit length
        
        return result
    
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
                "input_type": event_data.get("input_type", "text"),
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