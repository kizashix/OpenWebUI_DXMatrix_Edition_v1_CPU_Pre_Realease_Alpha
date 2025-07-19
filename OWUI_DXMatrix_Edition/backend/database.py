"""
Open WebUI DXMatrix Edition - Windows Native Database Module
SQLite-based database for sessions, caching, and application data
"""

import sqlite3
import json
import os
import time
import threading
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for Windows-native Open WebUI"""
    
    def __init__(self, db_path: str = None):
        """Initialize SQLite database connection"""
        if db_path is None:
            # Use Windows AppData directory
            app_data = Path(os.environ.get('LOCALAPPDATA', 'C:/Users/Admin/AppData/Local'))
            db_path = app_data / "owui-dxmatrix" / "data" / "owui-dxmatrix.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-local storage for connections
        self._local = threading.local()
        
        # Initialize database
        self._init_database()
        logger.info(f"Database initialized at: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            # Enable foreign keys and WAL mode for better performance
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            self._local.connection.execute("PRAGMA synchronous = NORMAL")
            self._local.connection.execute("PRAGMA cache_size = 10000")
            self._local.connection.execute("PRAGMA temp_store = MEMORY")
        return self._local.connection

    def _init_database(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        # Cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT,
                role TEXT DEFAULT 'user',
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Application settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Chat history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                messages TEXT NOT NULL,
                model_config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_archived BOOLEAN DEFAULT 0,
                is_pinned BOOLEAN DEFAULT 0,
                folder_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at)")
        
        conn.commit()
        logger.info("Database tables initialized successfully")

    def _cleanup_expired(self):
        """Clean up expired sessions and cache entries"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Clean expired sessions
        cursor.execute("DELETE FROM sessions WHERE expires_at < ?", (datetime.now(),))
        sessions_deleted = cursor.rowcount
        
        # Clean expired cache entries
        cursor.execute("DELETE FROM cache WHERE expires_at < ?", (datetime.now(),))
        cache_deleted = cursor.rowcount
        
        conn.commit()
        
        if sessions_deleted > 0 or cache_deleted > 0:
            logger.info(f"Cleaned up {sessions_deleted} expired sessions and {cache_deleted} expired cache entries")

    # Session Management Methods
    def save_session(self, session_id: str, user_id: str, data: Dict[str, Any], 
                    expires_in: int = 3600) -> bool:
        """Save session data to database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            data_json = json.dumps(data)
            
            cursor.execute("""
                INSERT OR REPLACE INTO sessions 
                (session_id, user_id, data, updated_at, expires_at) 
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user_id, data_json, datetime.now(), expires_at))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data by session ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data, expires_at FROM sessions 
                WHERE session_id = ? AND (expires_at IS NULL OR expires_at > ?)
            """, (session_id, datetime.now()))
            
            result = cursor.fetchone()
            if result:
                data_json, expires_at = result
                # Update last accessed time
                cursor.execute("""
                    UPDATE sessions SET updated_at = ? WHERE session_id = ?
                """, (datetime.now(), session_id))
                conn.commit()
                return json.loads(data_json)
            return None
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete session by session ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, data, created_at, updated_at, expires_at 
                FROM sessions 
                WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY updated_at DESC
            """, (user_id, datetime.now()))
            
            sessions = []
            for row in cursor.fetchall():
                session_id, data_json, created_at, updated_at, expires_at = row
                sessions.append({
                    'session_id': session_id,
                    'data': json.loads(data_json),
                    'created_at': created_at,
                    'updated_at': updated_at,
                    'expires_at': expires_at
                })
            return sessions
        except Exception as e:
            logger.error(f"Error retrieving sessions for user {user_id}: {e}")
            return []

    # Cache Management Methods
    def set_cache(self, key: str, value: Any, expires_in: int = 300) -> bool:
        """Set cache value with expiration"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            value_json = json.dumps(value)
            
            cursor.execute("""
                INSERT OR REPLACE INTO cache 
                (key, value, expires_at, last_accessed) 
                VALUES (?, ?, ?, ?)
            """, (key, value_json, expires_at, datetime.now()))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value by key"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value, expires_at FROM cache 
                WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
            """, (key, datetime.now()))
            
            result = cursor.fetchone()
            if result:
                value_json, expires_at = result
                # Update access count and last accessed time
                cursor.execute("""
                    UPDATE cache 
                    SET access_count = access_count + 1, last_accessed = ? 
                    WHERE key = ?
                """, (datetime.now(), key))
                conn.commit()
                return json.loads(value_json)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cache key {key}: {e}")
            return None

    def delete_cache(self, key: str) -> bool:
        """Delete cache entry by key"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    def clear_cache(self, pattern: str = None) -> int:
        """Clear cache entries, optionally matching a pattern"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if pattern:
                cursor.execute("DELETE FROM cache WHERE key LIKE ?", (f"%{pattern}%",))
            else:
                cursor.execute("DELETE FROM cache")
            
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Cleared {deleted_count} cache entries")
            return deleted_count
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    # User Management Methods
    def create_user(self, user_id: str, username: str, email: str = None, 
                   password_hash: str = None, role: str = "user") -> bool:
        """Create a new user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (user_id, username, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, email, password_hash, role))
            
            conn.commit()
            logger.info(f"Created user: {username}")
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f"User already exists: {username}")
            return False
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, email, role, permissions, 
                       created_at, updated_at, last_login, is_active
                FROM users WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'role': result[3],
                    'permissions': json.loads(result[4]) if result[4] else {},
                    'created_at': result[5],
                    'updated_at': result[6],
                    'last_login': result[7],
                    'is_active': bool(result[8])
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            return None

    def update_user_login(self, user_id: str) -> bool:
        """Update user's last login time"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET last_login = ?, updated_at = ? WHERE user_id = ?
            """, (datetime.now(), datetime.now(), user_id))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user login {user_id}: {e}")
            return False

    # Settings Management Methods
    def set_setting(self, key: str, value: Any, description: str = None) -> bool:
        """Set application setting"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            value_json = json.dumps(value)
            
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, description, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, value_json, description, datetime.now()))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting configuration {key}: {e}")
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            if result:
                return json.loads(result[0])
            return default
        except Exception as e:
            logger.error(f"Error retrieving setting {key}: {e}")
            return default

    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value (alias for set_setting)"""
        return self.set_setting(key, value)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value (alias for get_setting)"""
        return self.get_setting(key, default)

    def clear_config(self) -> bool:
        """Clear all configuration values"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM settings")
            conn.commit()
            
            logger.info("Configuration cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing configuration: {e}")
            return False

    # Database Maintenance Methods
    def vacuum(self):
        """Optimize database by removing unused space"""
        try:
            conn = self._get_connection()
            conn.execute("VACUUM")
            logger.info("Database vacuum completed")
        except Exception as e:
            logger.error(f"Error during database vacuum: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Count sessions
            cursor.execute("SELECT COUNT(*) FROM sessions")
            stats['sessions_count'] = cursor.fetchone()[0]
            
            # Count cache entries
            cursor.execute("SELECT COUNT(*) FROM cache")
            stats['cache_count'] = cursor.fetchone()[0]
            
            # Count users
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['users_count'] = cursor.fetchone()[0]
            
            # Count chats
            cursor.execute("SELECT COUNT(*) FROM chats")
            stats['chats_count'] = cursor.fetchone()[0]
            
            # Database file size
            stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    def close(self):
        """Close database connections"""
        try:
            if hasattr(self._local, 'connection'):
                self._local.connection.close()
                delattr(self._local, 'connection')
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


# Global database instance
_db_instance = None
_db_lock = threading.Lock()


def get_database() -> Database:
    """Get global database instance (thread-safe)"""
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = Database()
    return _db_instance


def close_database():
    """Close global database instance"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None 