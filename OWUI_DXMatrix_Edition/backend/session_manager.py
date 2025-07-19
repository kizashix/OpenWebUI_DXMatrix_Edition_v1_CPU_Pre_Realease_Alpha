"""
Open WebUI DXMatrix Edition - Windows Native Session Manager
Replaces Redis-based sessions with SQLite for Windows-native operation
"""

import uuid
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from database import get_database

logger = logging.getLogger(__name__)


class WindowsSessionManager:
    """Windows-native session manager using SQLite"""
    
    def __init__(self, session_timeout: int = 3600, cleanup_interval: int = 300):
        """
        Initialize session manager
        
        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
            cleanup_interval: Cleanup interval in seconds (default: 5 minutes)
        """
        self.session_timeout = session_timeout
        self.cleanup_interval = cleanup_interval
        self.db = get_database()
        
        # Start cleanup thread
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()
        
        logger.info(f"Windows Session Manager initialized (timeout: {session_timeout}s)")

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._stop_cleanup.clear()
            self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self._cleanup_thread.start()
            logger.info("Session cleanup thread started")

    def _cleanup_worker(self):
        """Background worker for cleaning up expired sessions"""
        while not self._stop_cleanup.wait(self.cleanup_interval):
            try:
                self._cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in session cleanup worker: {e}")

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            # This is handled by the database cleanup method
            self.db._cleanup_expired()
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")

    def create_session(self, user_id: str, user_data: Dict[str, Any] = None) -> str:
        """
        Create a new session for a user
        
        Args:
            user_id: User identifier
            user_data: Additional user data to store in session
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            session_data = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "data": user_data or {}
            }
            
            success = self.db.save_session(
                session_id, 
                user_id, 
                session_data, 
                expires_in=self.session_timeout
            )
            
            if success:
                logger.info(f"Created session {session_id} for user {user_id}")
                return session_id
            else:
                logger.error(f"Failed to create session for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data by session ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found/expired
        """
        try:
            session_data = self.db.get_session(session_id)
            
            if session_data:
                # Update last activity
                session_data["last_activity"] = datetime.now().isoformat()
                self.db.save_session(
                    session_id,
                    session_data.get("user_id", ""),
                    session_data,
                    expires_in=self.session_timeout
                )
                
                logger.debug(f"Retrieved session {session_id}")
                return session_data
            else:
                logger.debug(f"Session {session_id} not found or expired")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session identifier
            data: New session data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            existing_data = self.db.get_session(session_id)
            if existing_data:
                # Merge existing data with new data
                existing_data.update(data)
                existing_data["last_activity"] = datetime.now().isoformat()
                
                success = self.db.save_session(
                    session_id,
                    existing_data.get("user_id", ""),
                    existing_data,
                    expires_in=self.session_timeout
                )
                
                if success:
                    logger.debug(f"Updated session {session_id}")
                    return True
                else:
                    logger.error(f"Failed to update session {session_id}")
                    return False
            else:
                logger.warning(f"Session {session_id} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.db.delete_session(session_id)
            if success:
                logger.info(f"Deleted session {session_id}")
            else:
                logger.warning(f"Session {session_id} not found for deletion")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session data
        """
        try:
            sessions = self.db.get_user_sessions(user_id)
            logger.debug(f"Retrieved {len(sessions)} sessions for user {user_id}")
            return sessions
            
        except Exception as e:
            logger.error(f"Error retrieving sessions for user {user_id}: {e}")
            return []

    def is_session_valid(self, session_id: str) -> bool:
        """
        Check if a session is valid (exists and not expired)
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if valid, False otherwise
        """
        try:
            session_data = self.db.get_session(session_id)
            return session_data is not None
            
        except Exception as e:
            logger.error(f"Error checking session validity {session_id}: {e}")
            return False

    def extend_session(self, session_id: str, additional_time: int = None) -> bool:
        """
        Extend session timeout
        
        Args:
            session_id: Session identifier
            additional_time: Additional time in seconds (uses default timeout if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.db.get_session(session_id)
            if session_data:
                timeout = additional_time or self.session_timeout
                success = self.db.save_session(
                    session_id,
                    session_data.get("user_id", ""),
                    session_data,
                    expires_in=timeout
                )
                
                if success:
                    logger.debug(f"Extended session {session_id} by {timeout}s")
                    return True
                else:
                    logger.error(f"Failed to extend session {session_id}")
                    return False
            else:
                logger.warning(f"Session {session_id} not found for extension")
                return False
                
        except Exception as e:
            logger.error(f"Error extending session {session_id}: {e}")
            return False

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics
        
        Returns:
            Dictionary with session statistics
        """
        try:
            db_stats = self.db.get_stats()
            
            # Get active sessions count
            active_sessions = db_stats.get("sessions_count", 0)
            
            stats = {
                "total_sessions": active_sessions,
                "session_timeout": self.session_timeout,
                "cleanup_interval": self.cleanup_interval,
                "cleanup_thread_alive": self._cleanup_thread.is_alive() if self._cleanup_thread else False
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}

    def cleanup_all_sessions(self) -> int:
        """
        Clean up all expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            self._cleanup_expired_sessions()
            return 0  # The actual count is logged by the database cleanup method
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0

    def shutdown(self):
        """Shutdown the session manager"""
        try:
            # Stop cleanup thread
            self._stop_cleanup.set()
            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._cleanup_thread.join(timeout=5)
            
            logger.info("Session manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during session manager shutdown: {e}")


# Global session manager instance
_session_manager = None
_session_manager_lock = threading.Lock()


def get_session_manager() -> WindowsSessionManager:
    """Get global session manager instance (thread-safe)"""
    global _session_manager
    if _session_manager is None:
        with _session_manager_lock:
            if _session_manager is None:
                _session_manager = WindowsSessionManager()
    return _session_manager


def shutdown_session_manager():
    """Shutdown global session manager"""
    global _session_manager
    if _session_manager:
        _session_manager.shutdown()
        _session_manager = None


# FastAPI integration helpers
class SessionMiddleware:
    """FastAPI middleware for session management"""
    
    def __init__(self, app, session_manager: WindowsSessionManager = None):
        self.app = app
        self.session_manager = session_manager or get_session_manager()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract session ID from cookies or headers
            session_id = self._extract_session_id(scope)
            
            if session_id:
                # Validate and get session data
                session_data = self.session_manager.get_session(session_id)
                if session_data:
                    # Add session data to scope
                    scope["session"] = session_data
                    scope["session_id"] = session_id
                else:
                    # Invalid session, clear it
                    scope["session"] = None
                    scope["session_id"] = None
            else:
                scope["session"] = None
                scope["session_id"] = None

        await self.app(scope, receive, send)

    def _extract_session_id(self, scope) -> Optional[str]:
        """Extract session ID from request"""
        headers = dict(scope.get("headers", []))
        
        # Check for session cookie
        cookie_header = headers.get(b"cookie", b"").decode("utf-8")
        if "session_id=" in cookie_header:
            for cookie in cookie_header.split(";"):
                if "session_id=" in cookie:
                    return cookie.split("=")[1].strip()
        
        # Check for session header
        session_header = headers.get(b"x-session-id", b"").decode("utf-8")
        if session_header:
            return session_header
        
        return None


def require_session(func):
    """Decorator to require valid session for FastAPI endpoints"""
    async def wrapper(*args, **kwargs):
        # This would be implemented based on your FastAPI setup
        # For now, it's a placeholder for session validation
        return await func(*args, **kwargs)
    return wrapper 