"""
Open WebUI DXMatrix Edition - Windows Native Configuration Manager
Handles application configuration and settings for Windows-native operation
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime

from database import get_database

logger = logging.getLogger(__name__)


class WindowsConfigManager:
    """Windows-native configuration manager"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Configuration directory path (defaults to Windows AppData)
        """
        if config_dir is None:
            # Use Windows AppData directory
            app_data = Path(os.environ.get('LOCALAPPDATA', 'C:/Users/Admin/AppData/Local'))
            config_dir = app_data / "owui-dxmatrix" / "config"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration file paths
        self.config_file = self.config_dir / "config.json"
        self.environment_file = self.config_dir / "environment.yml"
        self.logs_dir = self.config_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Database for persistent settings
        self.db = get_database()
        
        # Load default configuration
        self._load_default_config()
        
        # Load existing configuration
        self._load_config()
        
        logger.info(f"Configuration manager initialized at: {self.config_dir}")

    def _load_default_config(self):
        """Load default configuration values"""
        self.default_config = {
            "app": {
                "name": "Open WebUI DXMatrix Edition",
                "version": "1.0.0",
                "debug": False,
                "host": "127.0.0.1",
                "port": 3000,
                "workers": 1
            },
            "database": {
                "type": "sqlite",
                "path": str(self.config_dir.parent / "data" / "owui-dxmatrix.db"),
                "backup_enabled": True,
                "backup_interval": 86400,  # 24 hours
                "max_backups": 7
            },
            "session": {
                "timeout": 3600,  # 1 hour
                "cleanup_interval": 300,  # 5 minutes
                "secure_cookies": False,
                "http_only": True
            },
            "security": {
                "secret_key": self._generate_secret_key(),
                "password_min_length": 8,
                "max_login_attempts": 5,
                "lockout_duration": 900,  # 15 minutes
                "enable_csrf": True,
                "enable_rate_limiting": True,
                "rate_limit_requests": 100,
                "rate_limit_window": 60  # 1 minute
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "file_path": str(self.logs_dir / "owui-dxmatrix.log"),
                "max_file_size": 10485760,  # 10 MB
                "backup_count": 5,
                "console_enabled": True
            },
            "features": {
                "enable_registration": True,
                "enable_password_reset": True,
                "enable_email_verification": False,
                "enable_2fa": False,
                "enable_api_keys": True,
                "enable_file_upload": True,
                "max_file_size": 10485760,  # 10 MB
                "allowed_file_types": [".txt", ".pdf", ".doc", ".docx", ".jpg", ".png"]
            },
            "ui": {
                "theme": "default",
                "language": "en",
                "timezone": "UTC",
                "date_format": "%Y-%m-%d",
                "time_format": "%H:%M:%S"
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl": 300,  # 5 minutes
                "max_cache_size": 1000000,  # 1 MB
                "enable_compression": True,
                "enable_caching_headers": True
            },
            "windows": {
                "startup_enabled": False,
                "system_tray_enabled": True,
                "minimize_to_tray": True,
                "auto_update_enabled": False,
                "firewall_rule_name": "Open WebUI DXMatrix Edition",
                "service_name": "OWUI-DXMatrix",
                "service_display_name": "Open WebUI DXMatrix Edition Service"
            }
        }

    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        import secrets
        return secrets.token_urlsafe(32)

    def _load_config(self):
        """Load configuration from file and database"""
        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                self.config = self._merge_config(self.default_config, file_config)
                logger.info("Configuration loaded from file")
            except Exception as e:
                logger.error(f"Error loading configuration file: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self._save_config_file()

        # Load environment-specific settings
        self._load_environment_config()

    def _load_environment_config(self):
        """Load environment-specific configuration"""
        if self.environment_file.exists():
            try:
                with open(self.environment_file, 'r', encoding='utf-8') as f:
                    env_config = yaml.safe_load(f) or {}
                
                # Override config with environment settings
                self.config = self._merge_config(self.config, env_config)
                logger.info("Environment configuration loaded")
            except Exception as e:
                logger.error(f"Error loading environment configuration: {e}")

    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result

    def _save_config_file(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("Configuration saved to file")
        except Exception as e:
            logger.error(f"Error saving configuration file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot notation key
        
        Args:
            key: Configuration key (e.g., "app.host", "security.secret_key")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception as e:
            logger.error(f"Error getting configuration key {key}: {e}")
            return default

    def set(self, key: str, value: Any, persistent: bool = True) -> bool:
        """
        Set configuration value
        
        Args:
            key: Configuration key (e.g., "app.host")
            value: Configuration value
            persistent: Whether to save to database (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key.split('.')
            config = self.config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            # Save to database if persistent
            if persistent:
                success = self.db.set_setting(f"config.{key}", value, f"Configuration: {key}")
                if not success:
                    logger.error(f"Failed to save configuration {key} to database")
                    return False
            
            logger.debug(f"Configuration {key} set to {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting configuration key {key}: {e}")
            return False

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config.copy()

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values (alias for get_all)"""
        return self.get_all()

    def get_config_path(self) -> str:
        """Get the configuration directory path"""
        return str(self.config_dir)

    def exists(self, key: str) -> bool:
        """
        Check if configuration key exists
        
        Args:
            key: Configuration key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            keys = key.split('.')
            current = self.config
            
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return False
            
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """
        Delete configuration key
        
        Args:
            key: Configuration key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key.split('.')
            current = self.config
            
            # Navigate to parent of target key
            for k in keys[:-1]:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return False
            
            # Delete the key
            if isinstance(current, dict) and keys[-1] in current:
                del current[keys[-1]]
                
                # Save to database if persistent
                self.db.set_config(key, None)
                
                # Save to file
                self._save_config_file()
                
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting config key {key}: {e}")
            return False

    def reset_config(self) -> bool:
        """
        Reset configuration to defaults
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config = self.default_config.copy()
            self._save_config_file()
            
            # Clear database config
            self.db.clear_config()
            
            logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            return False

    def update(self, updates: Dict[str, Any], persistent: bool = True) -> bool:
        """
        Update multiple configuration values
        
        Args:
            updates: Dictionary of configuration updates
            persistent: Whether to save to database (default: True)
            
        Returns:
        True if successful, False otherwise
        """
        try:
            success = True
            
            for key, value in updates.items():
                if not self.set(key, value, persistent):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False

    def reset_to_default(self, key: str = None) -> bool:
        """
        Reset configuration to default values
        
        Args:
            key: Specific key to reset (if None, resets all)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if key is None:
                # Reset all configuration
                self.config = self.default_config.copy()
                self._save_config_file()
                
                # Clear database settings
                self.db.clear_cache("config.")
                
                logger.info("Configuration reset to defaults")
            else:
                # Reset specific key
                keys = key.split('.')
                default_value = self.default_config
                
                for k in keys:
                    if isinstance(default_value, dict) and k in default_value:
                        default_value = default_value[k]
                    else:
                        logger.warning(f"Default value not found for key {key}")
                        return False
                
                self.set(key, default_value)
                logger.info(f"Configuration {key} reset to default")
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            return False

    def export_config(self, file_path: str = None) -> bool:
        """
        Export configuration to file
        
        Args:
            file_path: Export file path (defaults to config directory)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if file_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = self.config_dir / f"config_export_{timestamp}.json"
            
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "version": self.get("app.version"),
                "configuration": self.config
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return False

    def import_config(self, file_path: str, merge: bool = True) -> bool:
        """
        Import configuration from file
        
        Args:
            file_path: Import file path
            merge: Whether to merge with existing config (True) or replace (False)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if "configuration" in import_data:
                imported_config = import_data["configuration"]
                
                if merge:
                    self.config = self._merge_config(self.config, imported_config)
                else:
                    self.config = imported_config
                
                self._save_config_file()
                logger.info(f"Configuration imported from {file_path}")
                return True
            else:
                logger.error("Invalid configuration file format")
                return False
                
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False

    def validate_config(self) -> Dict[str, Any]:
        """
        Validate configuration values
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Validate required fields
            required_fields = [
                "app.name", "app.host", "app.port",
                "security.secret_key", "database.path"
            ]
            
            for field in required_fields:
                value = self.get(field)
                if value is None or value == "":
                    validation_results["errors"].append(f"Missing required field: {field}")
                    validation_results["valid"] = False
            
            # Validate port number
            port = self.get("app.port")
            if not isinstance(port, int) or port < 1 or port > 65535:
                validation_results["errors"].append("Invalid port number")
                validation_results["valid"] = False
            
            # Validate file paths
            db_path = self.get("database.path")
            if db_path and not Path(db_path).parent.exists():
                validation_results["warnings"].append(f"Database directory does not exist: {Path(db_path).parent}")
            
            # Validate security settings
            secret_key = self.get("security.secret_key")
            if len(secret_key) < 32:
                validation_results["warnings"].append("Secret key is shorter than recommended (32 characters)")
            
            logger.info(f"Configuration validation completed: {len(validation_results['errors'])} errors, {len(validation_results['warnings'])} warnings")
            
        except Exception as e:
            validation_results["errors"].append(f"Validation error: {e}")
            validation_results["valid"] = False
            logger.error(f"Error during configuration validation: {e}")
        
        return validation_results

    def get_windows_specific_config(self) -> Dict[str, Any]:
        """Get Windows-specific configuration"""
        return {
            "startup_enabled": self.get("windows.startup_enabled", False),
            "system_tray_enabled": self.get("windows.system_tray_enabled", True),
            "minimize_to_tray": self.get("windows.minimize_to_tray", True),
            "auto_update_enabled": self.get("windows.auto_update_enabled", False),
            "firewall_rule_name": self.get("windows.firewall_rule_name", "Open WebUI DXMatrix Edition"),
            "service_name": self.get("windows.service_name", "OWUI-DXMatrix"),
            "service_display_name": self.get("windows.service_display_name", "Open WebUI DXMatrix Edition Service"),
            "app_data_dir": str(self.config_dir.parent),
            "config_dir": str(self.config_dir),
            "logs_dir": str(self.logs_dir)
        }

    def create_environment_file(self, environment: str = "development") -> bool:
        """
        Create environment-specific configuration file
        
        Args:
            environment: Environment name (development, production, testing)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            env_config = {
                "environment": environment,
                "app": {
                    "debug": environment == "development"
                },
                "logging": {
                    "level": "DEBUG" if environment == "development" else "INFO"
                },
                "security": {
                    "enable_csrf": environment == "production",
                    "enable_rate_limiting": environment == "production"
                }
            }
            
            with open(self.environment_file, 'w', encoding='utf-8') as f:
                yaml.dump(env_config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Environment configuration file created for {environment}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating environment file: {e}")
            return False


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> WindowsConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = WindowsConfigManager()
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value (convenience function)"""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any, persistent: bool = True) -> bool:
    """Set configuration value (convenience function)"""
    return get_config_manager().set(key, value, persistent) 