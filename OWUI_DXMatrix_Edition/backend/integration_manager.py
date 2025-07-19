"""
Open WebUI DXMatrix Edition - Integration Manager
Handles the integration of Windows-native components with Open WebUI backend
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path

from database import get_database, close_database
from session_manager import get_session_manager, shutdown_session_manager
from config_manager import get_config_manager

logger = logging.getLogger(__name__)


class OpenWebUIIntegrationManager:
    """Manages integration between Windows-native components and Open WebUI"""
    
    def __init__(self):
        """Initialize the integration manager"""
        self.db = get_database()
        self.session_mgr = get_session_manager()
        self.config_mgr = get_config_manager()
        
        # Migration status tracking
        self.migration_completed = False
        
        logger.info("Open WebUI Integration Manager initialized")

    def migrate_config_from_redis(self, redis_config: Dict[str, Any]) -> bool:
        """
        Migrate configuration from Redis format to SQLite
        
        Args:
            redis_config: Configuration data from Redis
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Migrating configuration from Redis to SQLite...")
            
            # Map Redis configuration keys to our config manager
            config_mapping = {
                "auth": {
                    "api_key": {
                        "enable": redis_config.get("ENABLE_API_KEY", True),
                        "endpoint_restrictions": redis_config.get("ENABLE_API_KEY_ENDPOINT_RESTRICTIONS", False),
                        "allowed_endpoints": redis_config.get("API_KEY_ALLOWED_ENDPOINTS", "")
                    },
                    "jwt_expiry": redis_config.get("JWT_EXPIRES_IN", "-1")
                },
                "oauth": {
                    "enable_signup": redis_config.get("ENABLE_OAUTH_SIGNUP", False),
                    "merge_accounts_by_email": redis_config.get("OAUTH_MERGE_ACCOUNTS_BY_EMAIL", False),
                    "google": {
                        "client_id": redis_config.get("GOOGLE_CLIENT_ID", ""),
                        "client_secret": redis_config.get("GOOGLE_CLIENT_SECRET", ""),
                        "scope": redis_config.get("GOOGLE_OAUTH_SCOPE", "openid email profile"),
                        "redirect_uri": redis_config.get("GOOGLE_REDIRECT_URI", "")
                    },
                    "microsoft": {
                        "client_id": redis_config.get("MICROSOFT_CLIENT_ID", ""),
                        "client_secret": redis_config.get("MICROSOFT_CLIENT_SECRET", ""),
                        "tenant_id": redis_config.get("MICROSOFT_CLIENT_TENANT_ID", ""),
                        "scope": redis_config.get("MICROSOFT_OAUTH_SCOPE", "openid email profile"),
                        "redirect_uri": redis_config.get("MICROSOFT_REDIRECT_URI", "")
                    },
                    "github": {
                        "client_id": redis_config.get("GITHUB_CLIENT_ID", ""),
                        "client_secret": redis_config.get("GITHUB_CLIENT_SECRET", ""),
                        "scope": redis_config.get("GITHUB_CLIENT_SCOPE", "user:email"),
                        "redirect_uri": redis_config.get("GITHUB_CLIENT_REDIRECT_URI", "")
                    }
                },
                "ollama": {
                    "enable_api": redis_config.get("ENABLE_OLLAMA_API", True),
                    "base_urls": redis_config.get("OLLAMA_BASE_URLS", []),
                    "api_configs": redis_config.get("OLLAMA_API_CONFIGS", {})
                },
                "openai": {
                    "enable_api": redis_config.get("ENABLE_OPENAI_API", True),
                    "api_base_urls": redis_config.get("OPENAI_API_BASE_URLS", []),
                    "api_keys": redis_config.get("OPENAI_API_KEYS", []),
                    "api_configs": redis_config.get("OPENAI_API_CONFIGS", {})
                },
                "direct_connections": {
                    "enable": redis_config.get("ENABLE_DIRECT_CONNECTIONS", False)
                },
                "models": {
                    "enable_base_models_cache": redis_config.get("ENABLE_BASE_MODELS_CACHE", True)
                },
                "code_execution": {
                    "enable": redis_config.get("ENABLE_CODE_EXECUTION", False),
                    "engine": redis_config.get("CODE_EXECUTION_ENGINE", "jupyter"),
                    "jupyter_url": redis_config.get("CODE_EXECUTION_JUPYTER_URL", ""),
                    "jupyter_auth": redis_config.get("CODE_EXECUTION_JUPYTER_AUTH", ""),
                    "jupyter_timeout": redis_config.get("CODE_EXECUTION_JUPYTER_TIMEOUT", 30)
                },
                "image_generation": {
                    "enable": redis_config.get("ENABLE_IMAGE_GENERATION", False),
                    "engine": redis_config.get("IMAGE_GENERATION_ENGINE", "automatic1111"),
                    "model": redis_config.get("IMAGE_GENERATION_MODEL", ""),
                    "size": redis_config.get("IMAGE_SIZE", "512x512"),
                    "steps": redis_config.get("IMAGE_STEPS", 20)
                },
                "audio": {
                    "stt_engine": redis_config.get("AUDIO_STT_ENGINE", "whisper"),
                    "tts_engine": redis_config.get("AUDIO_TTS_ENGINE", "openai"),
                    "tts_model": redis_config.get("AUDIO_TTS_MODEL", "tts-1"),
                    "tts_voice": redis_config.get("AUDIO_TTS_VOICE", "alloy")
                },
                "retrieval": {
                    "rag_template": redis_config.get("RAG_TEMPLATE", ""),
                    "embedding_model": redis_config.get("RAG_EMBEDDING_MODEL", ""),
                    "full_context": redis_config.get("RAG_FULL_CONTEXT", False)
                }
            }
            
            # Save migrated configuration
            for section, section_data in config_mapping.items():
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            config_key = f"{section}.{key}.{subkey}"
                            self.config_mgr.set(config_key, subvalue, persistent=True)
                    else:
                        config_key = f"{section}.{key}"
                        self.config_mgr.set(config_key, value, persistent=True)
            
            logger.info("Configuration migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating configuration: {e}")
            return False

    def create_session_for_user(self, user_id: str, user_data: Dict[str, Any]) -> str:
        """
        Create a session for a user (compatible with Open WebUI auth)
        
        Args:
            user_id: User identifier
            user_data: User data to store in session
            
        Returns:
            Session ID
        """
        try:
            session_id = self.session_mgr.create_session(user_id, user_data)
            logger.info(f"Created session for user {user_id}")
            return session_id
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            return None

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session and return user data
        
        Args:
            session_id: Session identifier
            
        Returns:
            User data if valid, None otherwise
        """
        try:
            session_data = self.session_mgr.get_session(session_id)
            if session_data:
                return session_data.get("data", {})
            return None
        except Exception as e:
            logger.error(f"Error validating session {session_id}: {e}")
            return None

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value (compatible with Open WebUI config system)
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        try:
            return self.config_mgr.get(key, default)
        except Exception as e:
            logger.error(f"Error getting config value {key}: {e}")
            return default

    def set_config_value(self, key: str, value: Any) -> bool:
        """
        Set configuration value (compatible with Open WebUI config system)
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.config_mgr.set(key, value, persistent=True)
        except Exception as e:
            logger.error(f"Error setting config value {key}: {e}")
            return False

    def cache_set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set cache value (Redis-compatible interface)
        
        Args:
            key: Cache key
            value: Cache value
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.set_cache(key, value, expires_in=ttl)
        except Exception as e:
            logger.error(f"Error setting cache {key}: {e}")
            return False

    def cache_get(self, key: str) -> Any:
        """
        Get cache value (Redis-compatible interface)
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            return self.db.get_cache(key)
        except Exception as e:
            logger.error(f"Error getting cache {key}: {e}")
            return None

    def cache_delete(self, key: str) -> bool:
        """
        Delete cache value (Redis-compatible interface)
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.delete_cache(key)
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {e}")
            return False

    def get_user_sessions(self, user_id: str) -> list:
        """
        Get all sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session data
        """
        try:
            return self.session_mgr.get_user_sessions(user_id)
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []

    def delete_user_session(self, session_id: str) -> bool:
        """
        Delete a user session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.session_mgr.delete_session(session_id)
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        
        Returns:
            Dictionary with system statistics
        """
        try:
            db_stats = self.db.get_stats()
            session_stats = self.session_mgr.get_session_stats()
            config_stats = self.config_mgr.validate_config()
            
            return {
                "database": db_stats,
                "sessions": session_stats,
                "config": config_stats,
                "windows_native": True
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}

    def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired sessions and cache entries
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            # Clean up expired sessions
            session_cleanup = self.session_mgr.cleanup_all_sessions()
            
            # Clean up expired cache entries
            cache_cleanup = self.db.clear_cache()
            
            return {
                "sessions_cleaned": session_cleanup,
                "cache_entries_cleaned": cache_cleanup
            }
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"sessions_cleaned": 0, "cache_entries_cleaned": 0}

    def export_configuration(self, file_path: str = None) -> bool:
        """
        Export current configuration
        
        Args:
            file_path: Export file path (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.config_mgr.export_config(file_path)
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return False

    def import_configuration(self, file_path: str, merge: bool = True) -> bool:
        """
        Import configuration from file
        
        Args:
            file_path: Import file path
            merge: Whether to merge with existing config
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.config_mgr.import_config(file_path, merge)
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False

    def shutdown(self):
        """Shutdown the integration manager"""
        try:
            logger.info("Shutting down Open WebUI Integration Manager...")
            
            # Clean up resources
            close_database()
            shutdown_session_manager()
            
            logger.info("Integration Manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Global integration manager instance
_integration_manager = None


def get_integration_manager() -> OpenWebUIIntegrationManager:
    """Get global integration manager instance"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = OpenWebUIIntegrationManager()
    return _integration_manager


def shutdown_integration_manager():
    """Shutdown global integration manager"""
    global _integration_manager
    if _integration_manager:
        _integration_manager.shutdown()
        _integration_manager = None 