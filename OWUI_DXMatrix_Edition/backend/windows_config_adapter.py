"""
Open WebUI DXMatrix Edition - Windows Native Configuration Adapter
Replaces Redis-based configuration with SQLite-based configuration
"""

import json
import logging
from typing import Optional, Dict, Any, Union, Generic, TypeVar
from datetime import datetime

from config_manager import get_config_manager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class WindowsPersistentConfig(Generic[T]):
    """Windows-native persistent configuration (replaces Open WebUI's PersistentConfig)"""
    def __init__(self, env_name: str, config_path: str, env_value: T):
        object.__setattr__(self, '_env_name', env_name)
        object.__setattr__(self, '_config_path', config_path)
        object.__setattr__(self, '_config_mgr', get_config_manager())
        config_value = self._config_mgr.get(config_path)
        if config_value is not None:
            object.__setattr__(self, '_value', config_value)
        else:
            object.__setattr__(self, '_value', env_value)
            self._config_mgr.set(config_path, env_value, persistent=True)

    def __getattribute__(self, item):
        if item == 'value':
            return object.__getattribute__(self, '_value')
        return object.__getattribute__(self, item)

    def __setattr__(self, key, value):
        if key == 'value':
            object.__setattr__(self, '_value', value)
            self._config_mgr.set(self._config_path, value, persistent=True)
        else:
            object.__setattr__(self, key, value)

    def __str__(self):
        return str(object.__getattribute__(self, '_value'))

    def update(self):
        new_value = self._config_mgr.get(self._config_path)
        if new_value is not None:
            object.__setattr__(self, '_value', new_value)

    def save(self):
        self._config_mgr.set(self._config_path, object.__getattribute__(self, '_value'), persistent=True)


class WindowsAppConfig:
    def __init__(self, config_prefix: str = "open-webui"):
        # Use object.__setattr__ to set internal attributes without triggering __setattr__
        object.__setattr__(self, "_state", {})
        object.__setattr__(self, "_config_prefix", config_prefix)
        object.__setattr__(self, "config_mgr", get_config_manager())
        logger.info(f"Windows AppConfig initialized with prefix: {config_prefix}")

    def __setattr__(self, key, value):
        # Handle internal/special attributes directly
        if key.startswith("_") or key == "config_mgr":
            object.__setattr__(self, key, value)
        # Handle PersistentConfig objects
        elif isinstance(value, WindowsPersistentConfig):
            self._state[key] = value
        # Update existing config keys
        elif key in self._state:
            self._state[key].value = value
            self._state[key].save()
            config_key = f"{self._config_prefix}:config:{key}"
            self.config_mgr.set(config_key, value, persistent=True)
        # Fallback for non-config attributes
        else:
            object.__setattr__(self, key, value)

    def __getattr__(self, key):
        # Handle internal/special attributes directly
        if key.startswith("_") or key == "config_mgr":
            return object.__getattribute__(self, key)
        # Check if the key exists in the config state
        if key not in self._state:
            raise AttributeError(f"Config key '{key}' not found")
        # Sync with config manager if necessary
        config_key = f"{self._config_prefix}:config:{key}"
        config_value = self.config_mgr.get(config_key)
        if config_value is not None and self._state[key].value != config_value:
            self._state[key].value = config_value
            logger.info(f"Updated {key} from configuration: {config_value}")
        return self._state[key].value

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values"""
        result = {}
        for key, config in self._state.items():
            result[key] = config.value
        return result

    def set_config(self, key: str, value: Any):
        """Set a configuration value"""
        if key in self._state:
            self._state[key].value = value
            self._state[key].save()
            
            # Update in config manager
            config_key = f"{self._config_prefix}:config:{key}"
            self.config_mgr.set(config_key, value, persistent=True)
        else:
            raise AttributeError(f"Config key '{key}' not found")

    def reload_config(self):
        """Reload all configuration values from storage"""
        for key, config in self._state.items():
            config.update()


# Configuration factory functions
def create_persistent_config(env_name: str, config_path: str, env_value: T) -> WindowsPersistentConfig[T]:
    """Create a persistent configuration object"""
    return WindowsPersistentConfig(env_name, config_path, env_value)


def create_app_config(config_prefix: str = "open-webui") -> WindowsAppConfig:
    """Create an application configuration object"""
    return WindowsAppConfig(config_prefix)


# Open WebUI compatibility functions
def get_config_value(config_path: str, default: Any = None) -> Any:
    """
    Get configuration value (compatible with Open WebUI config system)
    
    Args:
        config_path: Configuration path (e.g., "auth.api_key.enable")
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    config_mgr = get_config_manager()
    return config_mgr.get(config_path, default)


def set_config_value(config_path: str, value: Any) -> bool:
    """
    Set configuration value (compatible with Open WebUI config system)
    
    Args:
        config_path: Configuration path
        value: Configuration value
        
    Returns:
        True if successful, False otherwise
    """
    config_mgr = get_config_manager()
    return config_mgr.set(config_path, value, persistent=True)


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save configuration (compatible with Open WebUI config system)
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if successful, False otherwise
    """
    config_mgr = get_config_manager()
    
    try:
        # Save each configuration item
        for key, value in config.items():
            config_mgr.set(key, value, persistent=True)
        
        logger.info("Configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False


def get_config() -> Dict[str, Any]:
    """
    Get all configuration (compatible with Open WebUI config system)
    
    Returns:
        Configuration dictionary
    """
    config_mgr = get_config_manager()
    return config_mgr.get_all_config()


def reset_config() -> bool:
    """
    Reset configuration to defaults (compatible with Open WebUI config system)
    
    Returns:
        True if successful, False otherwise
    """
    config_mgr = get_config_manager()
    
    try:
        config_mgr.reset_config()
        logger.info("Configuration reset to defaults")
        return True
    except Exception as e:
        logger.error(f"Error resetting configuration: {e}")
        return False


# Redis-compatible configuration functions
def redis_config_get(key: str, default: Any = None) -> Any:
    """
    Get configuration value (Redis-compatible interface)
    
    Args:
        key: Configuration key
        default: Default value
        
    Returns:
        Configuration value
    """
    return get_config_value(key, default)


def redis_config_set(key: str, value: Any) -> bool:
    """
    Set configuration value (Redis-compatible interface)
    
    Args:
        key: Configuration key
        value: Configuration value
        
    Returns:
        True if successful, False otherwise
    """
    return set_config_value(key, value)


def redis_config_delete(key: str) -> bool:
    """
    Delete configuration value (Redis-compatible interface)
    
    Args:
        key: Configuration key
        
    Returns:
        True if successful, False otherwise
    """
    config_mgr = get_config_manager()
    return config_mgr.delete(key)


def redis_config_exists(key: str) -> bool:
    """
    Check if configuration key exists (Redis-compatible interface)
    
    Args:
        key: Configuration key
        
    Returns:
        True if exists, False otherwise
    """
    config_mgr = get_config_manager()
    return config_mgr.exists(key)


# Configuration migration functions
def migrate_redis_config(redis_config: Dict[str, Any]) -> bool:
    """
    Migrate configuration from Redis format
    
    Args:
        redis_config: Redis configuration data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Migrating Redis configuration to Windows-native format...")
        
        config_mgr = get_config_manager()
        
        # Convert Redis configuration to our format
        for key, value in redis_config.items():
            # Handle nested configuration
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    config_key = f"{key}.{subkey}"
                    config_mgr.set(config_key, subvalue, persistent=True)
            else:
                config_mgr.set(key, value, persistent=True)
        
        logger.info("Redis configuration migration completed")
        return True
        
    except Exception as e:
        logger.error(f"Error migrating Redis configuration: {e}")
        return False


def export_config_to_redis_format() -> Dict[str, Any]:
    """
    Export configuration in Redis-compatible format
    
    Returns:
        Configuration in Redis format
    """
    config_mgr = get_config_manager()
    all_config = config_mgr.get_all_config()
    
    # Convert to Redis-compatible format
    redis_config = {}
    
    for key, value in all_config.items():
        # Handle nested keys (e.g., "auth.api_key.enable" -> {"auth": {"api_key": {"enable": value}}})
        parts = key.split('.')
        current = redis_config
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    return redis_config


# Configuration validation
def validate_config() -> Dict[str, Any]:
    """
    Validate configuration
    
    Returns:
        Validation results
    """
    config_mgr = get_config_manager()
    return config_mgr.validate_config()


# Configuration backup and restore
def backup_config(backup_path: str = None) -> bool:
    """
    Backup configuration
    
    Args:
        backup_path: Backup file path (optional)
        
    Returns:
        True if successful, False otherwise
    """
    config_mgr = get_config_manager()
    return config_mgr.export_config(backup_path)


def restore_config(backup_path: str, merge: bool = True) -> bool:
    """
    Restore configuration from backup
    
    Args:
        backup_path: Backup file path
        merge: Whether to merge with existing config
        
    Returns:
        True if successful, False otherwise
    """
    config_mgr = get_config_manager()
    return config_mgr.import_config(backup_path, merge) 