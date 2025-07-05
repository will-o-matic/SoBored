"""
Simple in-memory session manager for handling confirmation workflows.
This provides basic session storage for pending confirmations until a proper
Redis or database solution can be implemented.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import threading

@dataclass
class PendingConfirmation:
    """Data structure for a pending confirmation"""
    user_id: str
    chat_id: str
    timestamp: float
    event_data: Dict[str, Any]
    confirmation_message: str
    ttl_seconds: int = 300  # 5 minutes default TTL

class SessionManager:
    """
    Simple in-memory session manager for confirmation workflows.
    
    Note: This is a temporary solution. For production, use Redis or database.
    """
    
    def __init__(self):
        self._sessions: Dict[str, PendingConfirmation] = {}
        self._lock = threading.Lock()
    
    def store_pending_confirmation(
        self, 
        user_id: str, 
        chat_id: str, 
        event_data: Dict[str, Any],
        confirmation_message: str,
        ttl_seconds: int = 300
    ) -> str:
        """
        Store a pending confirmation for a user.
        
        Args:
            user_id: User identifier
            chat_id: Chat identifier  
            event_data: Extracted event data awaiting confirmation
            confirmation_message: The message shown to the user
            ttl_seconds: Time to live in seconds (default 5 minutes)
            
        Returns:
            Session key for this confirmation
        """
        session_key = f"{user_id}:{chat_id}"
        
        with self._lock:
            self._sessions[session_key] = PendingConfirmation(
                user_id=user_id,
                chat_id=chat_id,
                timestamp=time.time(),
                event_data=event_data,
                confirmation_message=confirmation_message,
                ttl_seconds=ttl_seconds
            )
        
        print(f"[SESSION] Stored pending confirmation for {session_key}")
        return session_key
    
    def get_pending_confirmation(self, user_id: str, chat_id: str) -> Optional[PendingConfirmation]:
        """
        Retrieve a pending confirmation for a user.
        
        Args:
            user_id: User identifier
            chat_id: Chat identifier
            
        Returns:
            PendingConfirmation if exists and not expired, None otherwise
        """
        session_key = f"{user_id}:{chat_id}"
        
        with self._lock:
            if session_key not in self._sessions:
                return None
            
            confirmation = self._sessions[session_key]
            
            # Check if expired
            if time.time() - confirmation.timestamp > confirmation.ttl_seconds:
                del self._sessions[session_key]
                print(f"[SESSION] Expired confirmation for {session_key}")
                return None
            
            return confirmation
    
    def confirm_and_remove(self, user_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Confirm a pending confirmation and remove it from storage.
        
        Args:
            user_id: User identifier
            chat_id: Chat identifier
            
        Returns:
            Event data if confirmation exists, None otherwise
        """
        session_key = f"{user_id}:{chat_id}"
        
        with self._lock:
            if session_key not in self._sessions:
                print(f"[SESSION] No session found for {session_key}")
                return None
            
            confirmation = self._sessions[session_key]
            
            # Check if expired
            if time.time() - confirmation.timestamp > confirmation.ttl_seconds:
                del self._sessions[session_key]
                print(f"[SESSION] Expired confirmation for {session_key}")
                return None
            
            # Get event data and remove session
            event_data = confirmation.event_data
            del self._sessions[session_key]
            print(f"[SESSION] Confirmed and removed session {session_key}")
            return event_data
    
    def cancel_confirmation(self, user_id: str, chat_id: str) -> bool:
        """
        Cancel a pending confirmation.
        
        Args:
            user_id: User identifier
            chat_id: Chat identifier
            
        Returns:
            True if confirmation was cancelled, False if not found
        """
        session_key = f"{user_id}:{chat_id}"
        
        with self._lock:
            if session_key in self._sessions:
                del self._sessions[session_key]
                print(f"[SESSION] Cancelled confirmation for {session_key}")
                return True
            
            return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from memory"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, confirmation in self._sessions.items():
                if current_time - confirmation.timestamp > confirmation.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._sessions[key]
        
        if expired_keys:
            print(f"[SESSION] Cleaned up {len(expired_keys)} expired sessions")
    
    def has_pending_confirmation(self, user_id: str, chat_id: str) -> bool:
        """
        Check if user has a pending confirmation.
        
        Args:
            user_id: User identifier
            chat_id: Chat identifier
            
        Returns:
            True if user has pending confirmation, False otherwise
        """
        return self.get_pending_confirmation(user_id, chat_id) is not None
    
    def get_session_count(self) -> int:
        """Get current number of active sessions"""
        with self._lock:
            return len(self._sessions)

# Global session manager instance
session_manager = SessionManager()

def is_confirmation_response(text: str) -> bool:
    """
    Check if a text message is likely a confirmation response.
    
    Args:
        text: Message text to check
        
    Returns:
        True if this looks like a confirmation response
    """
    if not text:
        return False
    
    text_lower = text.lower().strip()
    
    # Positive confirmations
    positive_responses = {
        'yes', 'y', 'confirm', 'ok', 'okay', 'correct', 'right', 'good', 
        'approve', 'accept', 'proceed', 'save', 'looks good', 'perfect',
        '✅', 'true', '1', 'affirmative', 'yep', 'yeah', 'yup'
    }
    
    # Negative confirmations  
    negative_responses = {
        'no', 'n', 'cancel', 'stop', 'abort', 'wrong', 'incorrect', 'bad',
        'reject', 'decline', 'dismiss', 'nevermind', 'never mind',
        '❌', 'false', '0', 'negative', 'nope', 'nah'
    }
    
    # Check for exact matches
    if text_lower in positive_responses or text_lower in negative_responses:
        return True
    
    # Check for edit commands (field: value)
    if ':' in text and any(field in text_lower for field in ['title', 'date', 'location', 'description']):
        return True
    
    return False

def parse_confirmation_response(text: str) -> Dict[str, Any]:
    """
    Parse a confirmation response to understand the user's intent.
    
    Args:
        text: Confirmation response text
        
    Returns:
        Dict with 'action' and other relevant fields
    """
    if not text:
        return {'action': 'unknown'}
    
    text_lower = text.lower().strip()
    
    # Positive confirmations
    positive_responses = {
        'yes', 'y', 'confirm', 'ok', 'okay', 'correct', 'right', 'good', 
        'approve', 'accept', 'proceed', 'save', 'looks good', 'perfect',
        '✅', 'true', '1', 'affirmative', 'yep', 'yeah', 'yup'
    }
    
    # Negative confirmations
    negative_responses = {
        'no', 'n', 'cancel', 'stop', 'abort', 'wrong', 'incorrect', 'bad',
        'reject', 'decline', 'dismiss', 'nevermind', 'never mind',
        '❌', 'false', '0', 'negative', 'nope', 'nah'
    }
    
    if text_lower in positive_responses:
        return {'action': 'confirm'}
    
    if text_lower in negative_responses:
        return {'action': 'cancel'}
    
    # Check for edit commands (field: value)
    if ':' in text:
        try:
            field, value = text.split(':', 1)
            field = field.strip().lower()
            value = value.strip()
            
            valid_fields = ['title', 'date', 'location', 'description']
            if field in valid_fields:
                return {
                    'action': 'edit',
                    'field': field,
                    'value': value
                }
        except:
            pass
    
    return {'action': 'unknown', 'original_text': text}