"""
Image processor for OCR-based event extraction from images
"""

import logging
import time
from typing import Dict, Any, Optional
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)

class ImageProcessor(BaseProcessor):
    """
    Processor for image-based event extraction using OCR
    
    Features:
    - OCR text extraction from images
    - Event parsing from extracted text
    - Multi-date and recurrence handling
    - Quality validation and confidence scoring
    - User confirmation workflow support
    """
    
    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run)
        self.processor_type = "image"
        self.ocr_stats = {
            "total_ocr_attempts": 0,
            "successful_ocr": 0,
            "failed_ocr": 0,
            "average_ocr_confidence": 0.0
        }
    
    def process(self, classified_input: Dict[str, Any], source: str = "telegram", 
                user_id: Optional[str] = None, parent_run=None) -> Dict[str, Any]:
        """
        Process image input and extract event data
        
        Args:
            classified_input: Output from SmartClassifier
            source: Source of the input
            user_id: Optional user identifier
            parent_run: Optional parent run context
            
        Returns:
            Dict containing extracted event data and metadata
        """
        start_time = time.time()
        
        try:
            # Create base result structure
            result = self._create_base_result(classified_input, source, user_id)
            
            # Extract image data from classified input
            image_data = classified_input.get("image_data")
            if not image_data:
                # For Telegram, we need to download the image first
                if source == "telegram":
                    image_data = self._download_telegram_image(classified_input)
                else:
                    raise ValueError("No image data provided in classified input")
            
            # Step 1: OCR text extraction from image
            logger.debug("Extracting text from image using OCR")
            ocr_result = self._extract_text_from_image(image_data)
            
            # Step 2: Validate OCR quality
            ocr_validation = self._validate_ocr_quality(ocr_result)
            
            # Step 3: Parse extracted text for event data
            if ocr_validation.get("is_reliable", False):
                logger.debug("Parsing OCR text for event data")
                parsed_result = self._parse_ocr_text(ocr_result["extracted_text"])
            else:
                # Handle poor OCR quality
                parsed_result = self._handle_poor_ocr_quality(ocr_result, ocr_validation)
            
            # Step 4: Validate extracted event data
            validation_result = self._validate_extracted_data(parsed_result)
            
            # Step 5: Check if user confirmation is needed
            confirmation_result = self._assess_confirmation_need(
                ocr_result, ocr_validation, parsed_result, validation_result
            )
            
            # Step 6: Save to Notion (or dry run) if no confirmation needed
            if not confirmation_result.get("confirmation_required", False):
                save_result = self._save_event_data({
                    **result,
                    **ocr_result,
                    **ocr_validation,
                    **parsed_result,
                    **validation_result
                })
            else:
                save_result = {
                    "notion_save_status": "pending_confirmation",
                    "notion_page_id": None,
                    "notion_url": None,
                    "pending_confirmation": True
                }
            
            # Combine all results
            final_result = {
                **result,
                **ocr_result,
                **ocr_validation,
                **parsed_result,
                **validation_result,
                **confirmation_result,
                **save_result,
                "processing_time": time.time() - start_time,
                "processor_type": self.processor_type
            }
            
            # Update statistics
            success = (save_result.get("notion_save_status") == "success" or 
                      save_result.get("pending_confirmation") or 
                      self.dry_run)
            self._update_stats(success, final_result["processing_time"])
            self._update_ocr_stats(ocr_result.get("success", False), 
                                  ocr_result.get("confidence", 0.0))
            
            logger.info(f"Image processing completed in {final_result['processing_time']:.2f}s")
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
            logger.error(f"Image processing failed: {e}")
            return error_result
    
    def _download_telegram_image(self, classified_input: Dict[str, Any]) -> str:
        """
        Download image from Telegram and return file path
        
        Args:
            classified_input: Input containing Telegram image data
            
        Returns:
            Local file path to downloaded image
        """
        try:
            # Extract image information from Telegram message
            telegram_data = classified_input.get("telegram_data", {})
            if not telegram_data:
                raise ValueError("No Telegram data provided for image download")
            
            # Get the largest photo size
            photos = telegram_data.get("photo", [])
            if not photos:
                raise ValueError("No photo data found in Telegram message")
            
            # Select highest resolution photo
            largest_photo = max(photos, key=lambda x: x.get("file_size", 0))
            file_id = largest_photo["file_id"]
            
            # Download using Telegram bot
            import os
            from telegram import Bot
            
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN not configured")
            
            bot = Bot(token=bot_token)
            
            # Get file information
            file_info = bot.get_file(file_id)
            
            # Create temporary file
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".jpg", 
                delete=False,
                dir="/tmp"
            )
            
            # Download image
            file_info.download(temp_file.name)
            
            logger.debug(f"Downloaded Telegram image to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to download Telegram image: {e}")
            raise
    
    def _extract_text_from_image(self, image_data: str) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Args:
            image_data: Image file path or URL
            
        Returns:
            Dict containing OCR results
        """
        try:
            # Use the OCR tool we created
            from langgraph.agents.tools.ocr_tool import extract_text_from_image
            
            result = extract_text_from_image.invoke({
                "image_data": image_data,
                "image_format": "auto"
            })
            
            logger.debug(f"OCR extraction completed: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_text": "",
                "confidence": 0.0
            }
    
    def _validate_ocr_quality(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate OCR quality and determine reliability
        
        Args:
            ocr_result: Result from OCR extraction
            
        Returns:
            Dict containing validation results
        """
        try:
            # Use the OCR validation tool
            from langgraph.agents.tools.ocr_tool import validate_ocr_quality
            
            validation_result = validate_ocr_quality.invoke({
                "ocr_result": ocr_result,
                "min_confidence": 70.0
            })
            
            logger.debug(f"OCR validation: {validation_result.get('is_reliable', False)}")
            return validation_result
            
        except Exception as e:
            logger.error(f"OCR validation failed: {e}")
            return {
                "is_reliable": False,
                "confidence": 0.0,
                "reason": f"Validation error: {str(e)}",
                "recommendation": "error"
            }
    
    def _parse_ocr_text(self, extracted_text: str) -> Dict[str, Any]:
        """
        Parse OCR-extracted text to extract event data
        
        Args:
            extracted_text: Text extracted from image via OCR
            
        Returns:
            Dict containing parsed event data
        """
        try:
            # Use the same LLM parsing as TextProcessor but with OCR-specific context
            result = self._llm_parse_ocr_text(extracted_text)
            
            # Enhance with processing metadata
            result["parsing_method"] = "llm_ocr"
            result["text_length"] = len(extracted_text)
            result["word_count"] = len(extracted_text.split())
            result["source_type"] = "ocr"
            
            return result
            
        except Exception as e:
            logger.error(f"OCR text parsing failed: {e}")
            return {
                "error": str(e),
                "parsing_confidence": 0.0,
                "parsing_method": "failed",
                "event_title": "",
                "event_date": "",
                "event_location": "",
                "event_description": extracted_text  # Fallback to original text
            }
    
    def _llm_parse_ocr_text(self, text: str) -> Dict[str, Any]:
        """
        Use LLM to parse OCR-extracted text for event data
        
        Args:
            text: OCR-extracted text content
            
        Returns:
            Dict containing extracted event information
        """
        try:
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
            This text was extracted from an image using OCR and may contain some errors or formatting issues. 
            Extract event information from the following text. Return a JSON object with these fields:
            - event_title: The name/title of the event
            - event_date: Date and time (YYYY-MM-DD HH:MM format - if multiple dates, separate with commas)
            - event_location: Venue/location of the event
            - event_description: Brief description of the event
            - parsing_confidence: Confidence score between 0.0 and 1.0
            - ocr_corrections: List of any obvious OCR errors you corrected
            
            IMPORTANT OCR CONTEXT:
            - This text came from an image and may have OCR errors
            - Common OCR mistakes: O/0, I/1/l, rn/m, etc.
            - Be flexible with spelling and formatting
            - Focus on extracting meaningful information despite potential errors
            
            IMPORTANT DATE CONTEXT:
            - Current date: {current_date_str}
            - Current year: {current_year}
            - When parsing dates without explicit years, assume the current year {current_year}
            - For dates that appear to be in the past but are likely future events, use {current_year}
            
            MULTI-DATE EXTRACTION RULES:
            - If you see EXPLICIT multiple dates listed (like "June 24, June 26, and June 28"), extract ALL dates
            - Format each date as YYYY-MM-DD HH:MM and separate with commas
            - Use the same time for all dates if only one time is specified
            - For RECURRING patterns (every X, weekly, daily for N weeks), extract only the START date
            - IMPORTANT: Only extract dates for the ACTUAL event, NOT mentioned dates like "rescheduled from" or "originally planned for"
            
            RECURRENCE PATTERN DETECTION:
            - Look for patterns like "every Monday", "weekly", "daily", "recurring"
            - If you detect a recurring pattern, mention it in event_description
            - Still only extract the START date in event_date field
            
            Examples:
              * "June 24, 26, 28 at 2PM" → "2025-06-24 14:00, 2025-06-26 14:00, 2025-06-28 14:00"
              * "Workshop on June 15 and June 17 at 10AM" → "2025-06-15 10:00, 2025-06-17 10:00"
              * "Meeting every Tuesday for 3 weeks starting June 24" → "2025-06-24 00:00" (recurring)
              * "Daily sessions June 24-27" → "2025-06-24 00:00, 2025-06-25 00:00, 2025-06-26 00:00, 2025-06-27 00:00"
            
            If any information is not available, use empty string for that field.
            
            OCR-extracted text to parse:
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
            logger.error(f"LLM OCR text parsing failed: {e}")
            # Fallback to simple extraction
            return self._simple_ocr_extraction(text)
    
    def _handle_poor_ocr_quality(self, ocr_result: Dict[str, Any], 
                                ocr_validation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle cases where OCR quality is poor
        
        Args:
            ocr_result: Original OCR results
            ocr_validation: OCR quality validation results
            
        Returns:
            Dict with appropriate handling strategy
        """
        recommendation = ocr_validation.get("recommendation", "error")
        
        if recommendation == "image_quality_poor":
            return {
                "error": "Image quality too poor for reliable text extraction",
                "parsing_confidence": 0.0,
                "parsing_method": "failed_poor_quality",
                "event_title": "",
                "event_date": "",
                "event_location": "",
                "event_description": "Image quality insufficient for OCR",
                "requires_user_input": True,
                "user_message": "The image quality is too poor for automatic text extraction. Could you please provide the event details manually or upload a clearer image?"
            }
        
        elif recommendation == "no_text_detected":
            return {
                "error": "No text detected in image",
                "parsing_confidence": 0.0,
                "parsing_method": "failed_no_text",
                "event_title": "",
                "event_date": "",
                "event_location": "",
                "event_description": "No text found in image",
                "requires_user_input": True,
                "user_message": "I couldn't detect any text in this image. Could you please provide the event details manually or verify the image contains readable text?"
            }
        
        else:
            # Try to parse anyway with low confidence
            extracted_text = ocr_result.get("extracted_text", "")
            if extracted_text:
                result = self._simple_ocr_extraction(extracted_text)
                result["parsing_confidence"] = min(result.get("parsing_confidence", 0.0), 0.4)
                result["low_confidence_warning"] = True
                return result
            else:
                return {
                    "error": "OCR extraction failed",
                    "parsing_confidence": 0.0,
                    "parsing_method": "failed",
                    "event_title": "",
                    "event_date": "",
                    "event_location": "",
                    "event_description": "",
                    "requires_user_input": True
                }
    
    def _assess_confirmation_need(self, ocr_result: Dict[str, Any], 
                                 ocr_validation: Dict[str, Any],
                                 parsed_result: Dict[str, Any],
                                 validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess whether user confirmation is needed before saving
        
        Args:
            ocr_result: OCR extraction results
            ocr_validation: OCR quality validation
            parsed_result: Parsed event data
            validation_result: Event data validation
            
        Returns:
            Dict with confirmation assessment
        """
        confirmation_required = False
        confirmation_reasons = []
        
        # Check OCR confidence
        ocr_confidence = ocr_result.get("confidence", 0.0)
        if ocr_confidence < 80:
            confirmation_required = True
            confirmation_reasons.append("low_ocr_confidence")
        
        # Check parsing confidence
        parsing_confidence = parsed_result.get("parsing_confidence", 0.0)
        if parsing_confidence < 0.7:
            confirmation_required = True
            confirmation_reasons.append("low_parsing_confidence")
        
        # Check validation score
        validation_score = validation_result.get("validation_score", 0.0)
        if validation_score < 0.6:
            confirmation_required = True
            confirmation_reasons.append("incomplete_event_data")
        
        # Check for special patterns that always need confirmation
        event_title = parsed_result.get("event_title", "")
        event_date = parsed_result.get("event_date", "")
        
        # Multi-date events should be confirmed
        if "," in event_date:
            confirmation_required = True
            confirmation_reasons.append("multiple_dates_detected")
        
        # Check for recurring patterns
        event_description = parsed_result.get("event_description", "")
        recurring_keywords = ["every", "weekly", "daily", "recurring", "series"]
        if any(keyword in event_description.lower() for keyword in recurring_keywords):
            confirmation_required = True
            confirmation_reasons.append("recurring_pattern_detected")
        
        # Generate user-friendly confirmation message
        if confirmation_required:
            confirmation_message = self._generate_confirmation_message(
                parsed_result, confirmation_reasons
            )
        else:
            confirmation_message = ""
        
        return {
            "confirmation_required": confirmation_required,
            "confirmation_reasons": confirmation_reasons,
            "confirmation_message": confirmation_message,
            "auto_save_confidence": not confirmation_required
        }
    
    def _generate_confirmation_message(self, parsed_result: Dict[str, Any], 
                                     reasons: list) -> str:
        """
        Generate user-friendly confirmation message
        
        Args:
            parsed_result: Parsed event data
            reasons: List of reasons for confirmation
            
        Returns:
            Formatted confirmation message
        """
        event_title = parsed_result.get("event_title", "Event")
        event_date = parsed_result.get("event_date", "Date TBD")
        event_location = parsed_result.get("event_location", "Location TBD")
        event_description = parsed_result.get("event_description", "")
        
        message = f"📋 **Please confirm the event details I extracted from your image:**\n\n"
        message += f"**Title:** {event_title}\n"
        message += f"**Date(s):** {event_date}\n"
        message += f"**Location:** {event_location}\n"
        
        if event_description:
            message += f"**Description:** {event_description[:200]}{'...' if len(event_description) > 200 else ''}\n"
        
        message += f"\n"
        
        # Add specific guidance based on reasons
        if "multiple_dates_detected" in reasons:
            message += "⚠️ I detected multiple dates. Please verify these are correct.\n"
        
        if "recurring_pattern_detected" in reasons:
            message += "🔄 This appears to be a recurring event. Please confirm the pattern.\n"
        
        if "low_ocr_confidence" in reasons:
            message += "👀 The image text was a bit unclear. Please double-check the details.\n"
        
        message += "\n**Reply with:**\n"
        message += "✅ 'Yes' or 'Confirm' to save as-is\n"
        message += "✏️ 'Edit [field]: [new value]' to make changes\n"
        message += "❌ 'Cancel' to discard\n"
        
        return message
    
    def _extract_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract event data from LLM response if JSON parsing fails
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Dict containing extracted data
        """
        # Same as TextProcessor but with OCR context
        lines = response_text.split('\n')
        result = {
            "event_title": "",
            "event_date": "",
            "event_location": "",
            "event_description": "",
            "parsing_confidence": 0.5,
            "ocr_corrections": []
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
    
    def _simple_ocr_extraction(self, text: str) -> Dict[str, Any]:
        """
        Simple pattern-based extraction from OCR text as fallback
        
        Args:
            text: OCR-extracted text
            
        Returns:
            Dict containing basic extracted data
        """
        # Similar to TextProcessor but adapted for OCR text
        from langgraph.pipeline.classifiers.patterns import TEXT_PATTERNS
        
        result = {
            "event_title": "",
            "event_date": "",
            "event_location": "",
            "event_description": text,
            "parsing_confidence": 0.3,
            "parsing_method": "ocr_pattern_fallback"
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
        
        # Use first line/sentence as title if available
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if first_line:
                result["event_title"] = first_line[:100]  # Limit length
        
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
                "input_type": event_data.get("input_type", "image"),
                "raw_input": event_data.get("raw_input", ""),
                "source": event_data.get("source", "pipeline"),
                "event_title": event_data.get("event_title", ""),
                "event_date": event_data.get("event_date", ""),
                "event_location": event_data.get("event_location", ""),
                "event_description": event_data.get("event_description", ""),
                "user_id": event_data.get("user_id"),
                "ocr_confidence": event_data.get("confidence", 0.0),
                "parsing_confidence": event_data.get("parsing_confidence", 0.0)
            }
            
            # Set environment variable for dry-run mode if needed
            import os
            if self.dry_run:
                os.environ["DRY_RUN"] = "true"
            else:
                os.environ["DRY_RUN"] = "false"
            
            # Use unified save tool that respects DRY_RUN environment variable
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
    
    def _update_ocr_stats(self, success: bool, confidence: float):
        """Update OCR-specific statistics"""
        self.ocr_stats["total_ocr_attempts"] += 1
        
        if success:
            self.ocr_stats["successful_ocr"] += 1
            # Update average confidence
            total = self.ocr_stats["successful_ocr"]
            current_avg = self.ocr_stats["average_ocr_confidence"]
            self.ocr_stats["average_ocr_confidence"] = (
                (current_avg * (total - 1) + confidence) / total
            )
        else:
            self.ocr_stats["failed_ocr"] += 1
    
    def get_ocr_stats(self) -> Dict[str, Any]:
        """Get OCR-specific statistics"""
        total = self.ocr_stats["total_ocr_attempts"]
        if total == 0:
            return {"message": "No OCR attempts yet"}
            
        return {
            **self.ocr_stats,
            "ocr_success_rate": (self.ocr_stats["successful_ocr"] / total) * 100,
            "ocr_failure_rate": (self.ocr_stats["failed_ocr"] / total) * 100
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        base_stats = super().get_stats()
        ocr_stats = self.get_ocr_stats()
        
        if isinstance(base_stats, dict) and "message" not in base_stats:
            return {
                **base_stats,
                "ocr_stats": ocr_stats
            }
        
        return {
            "processing_stats": base_stats,
            "ocr_stats": ocr_stats
        }