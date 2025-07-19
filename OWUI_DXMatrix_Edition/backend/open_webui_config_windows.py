"""
Open WebUI DXMatrix Edition - Windows Native Configuration
Replaces Redis-based configuration with SQLite-based configuration
"""

import json
import logging
import os
import shutil
import base64

from datetime import datetime
from pathlib import Path
from typing import Generic, Optional, TypeVar
from urllib.parse import urlparse

import requests
from pydantic import BaseModel
from sqlalchemy import JSON, Column, DateTime, Integer, func
from authlib.integrations.starlette_client import OAuth

# Import our Windows-native components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'OWUI_DXMatrix_Edition', 'backend'))

from windows_config_adapter import (
    WindowsPersistentConfig,
    WindowsAppConfig,
    get_config_value,
    set_config_value,
    save_config,
    get_config,
    reset_config
)
from integration_manager import get_integration_manager

# Import original Open WebUI environment variables
from open_webui.env import (
    DATA_DIR,
    DATABASE_URL,
    ENV,
    FRONTEND_BUILD_DIR,
    OFFLINE_MODE,
    OPEN_WEBUI_DIR,
    WEBUI_AUTH,
    WEBUI_FAVICON_URL,
    WEBUI_NAME,
    log,
)
from open_webui.internal.db import Base, get_db


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/health") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

####################################
# Config helpers
####################################


# Function to run the alembic migrations
def run_migrations():
    log.info("Running migrations")
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")

        # Set the script location dynamically
        migrations_path = OPEN_WEBUI_DIR / "migrations"
        alembic_cfg.set_main_option("script_location", str(migrations_path))

        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        log.exception(f"Error running migrations: {e}")


run_migrations()


class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    data = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


def load_json_config():
    with open(f"{DATA_DIR}/config.json", "r") as file:
        return json.load(file)


def save_to_db(data):
    with get_db() as db:
        existing_config = db.query(Config).first()
        if not existing_config:
            new_config = Config(data=data, version=0)
            db.add(new_config)
        else:
            existing_config.data = data
            existing_config.updated_at = datetime.now()
            db.add(existing_config)
        db.commit()


def reset_config_db():
    with get_db() as db:
        db.query(Config).delete()
        db.commit()


# When initializing, check if config.json exists and migrate it to the database
if os.path.exists(f"{DATA_DIR}/config.json"):
    data = load_json_config()
    save_to_db(data)
    os.rename(f"{DATA_DIR}/config.json", f"{DATA_DIR}/old_config.json")

DEFAULT_CONFIG = {
    "version": 0,
    "ui": {},
}


def get_config_from_db():
    with get_db() as db:
        config_entry = db.query(Config).order_by(Config.id.desc()).first()
        return config_entry.data if config_entry else DEFAULT_CONFIG


CONFIG_DATA = get_config_from_db()


def get_config_value_from_db(config_path: str):
    path_parts = config_path.split(".")
    cur_config = CONFIG_DATA
    for key in path_parts:
        if key in cur_config:
            cur_config = cur_config[key]
        else:
            return None
    return cur_config


PERSISTENT_CONFIG_REGISTRY = []


def save_config_to_db(config):
    global CONFIG_DATA
    global PERSISTENT_CONFIG_REGISTRY
    try:
        save_to_db(config)
        CONFIG_DATA = config

        # Trigger updates on all registered PersistentConfig entries
        for config_item in PERSISTENT_CONFIG_REGISTRY:
            config_item.update()
    except Exception as e:
        log.exception(e)
        return False
    return True


T = TypeVar("T")

ENABLE_PERSISTENT_CONFIG = (
    os.environ.get("ENABLE_PERSISTENT_CONFIG", "True").lower() == "true"
)


# Use our Windows-native PersistentConfig instead of the original
class PersistentConfig(Generic[T]):
    def __init__(self, env_name: str, config_path: str, env_value: T):
        self.env_name = env_name
        self.config_path = config_path
        self.env_value = env_value
        
        # Use our Windows-native config manager
        config_value = get_config_value(config_path)
        if config_value is not None and ENABLE_PERSISTENT_CONFIG:
            log.info(f"'{env_name}' loaded from Windows-native configuration: {config_value}")
            self.value = config_value
        else:
            self.value = env_value
            # Save the environment value to our config
            set_config_value(config_path, env_value)

        PERSISTENT_CONFIG_REGISTRY.append(self)

    def __str__(self):
        return str(self.value)

    @property
    def __dict__(self):
        raise TypeError(
            "PersistentConfig object cannot be converted to dict, use config_get or .value instead."
        )

    def __getattribute__(self, item):
        if item == "__dict__":
            raise TypeError(
                "PersistentConfig object cannot be converted to dict, use config_get or .value instead."
            )
        return super().__getattribute__(item)

    def update(self):
        new_value = get_config_value(self.config_path)
        if new_value is not None:
            self.value = new_value
            log.info(f"Updated {self.env_name} to new value {self.value}")

    def save(self):
        set_config_value(self.config_path, self.value)


# Use our Windows-native AppConfig instead of the Redis-based one
class AppConfig:
    _state: dict[str, PersistentConfig]
    _config_prefix: str

    def __init__(
        self,
        config_prefix: str = "open-webui",
    ):
        super().__setattr__("_state", {})
        super().__setattr__("_config_prefix", config_prefix)
        log.info(f"Windows-native AppConfig initialized with prefix: {config_prefix}")

    def __setattr__(self, key, value):
        if isinstance(value, PersistentConfig):
            self._state[key] = value
        else:
            if key in self._state:
                self._state[key].value = value
                self._state[key].save()
                
                # Update in our Windows-native config manager
                config_key = f"{self._config_prefix}:config:{key}"
                set_config_value(config_key, value)
            else:
                super().__setattr__(key, value)

    def __getattr__(self, key):
        if key not in self._state:
            raise AttributeError(f"Config key '{key}' not found")

        # Check for updated value in our Windows-native config manager
        config_key = f"{self._config_prefix}:config:{key}"
        config_value = get_config_value(config_key)

        if config_value is not None:
            # Update the in-memory value if different
            if self._state[key].value != config_value:
                self._state[key].value = config_value
                log.info(f"Updated {key} from Windows-native config: {config_value}")

        return self._state[key].value


####################################
# WEBUI_AUTH (Required for security)
####################################

ENABLE_API_KEY = PersistentConfig(
    "ENABLE_API_KEY",
    "auth.api_key.enable",
    os.environ.get("ENABLE_API_KEY", "True").lower() == "true",
)

ENABLE_API_KEY_ENDPOINT_RESTRICTIONS = PersistentConfig(
    "ENABLE_API_KEY_ENDPOINT_RESTRICTIONS",
    "auth.api_key.endpoint_restrictions",
    os.environ.get("ENABLE_API_KEY_ENDPOINT_RESTRICTIONS", "False").lower() == "true",
)

API_KEY_ALLOWED_ENDPOINTS = PersistentConfig(
    "API_KEY_ALLOWED_ENDPOINTS",
    "auth.api_key.allowed_endpoints",
    os.environ.get("API_KEY_ALLOWED_ENDPOINTS", ""),
)

JWT_EXPIRES_IN = PersistentConfig(
    "JWT_EXPIRES_IN", "auth.jwt_expiry", os.environ.get("JWT_EXPIRES_IN", "-1")
)

####################################
# OAuth config
####################################

ENABLE_OAUTH_SIGNUP = PersistentConfig(
    "ENABLE_OAUTH_SIGNUP",
    "oauth.enable_signup",
    os.environ.get("ENABLE_OAUTH_SIGNUP", "False").lower() == "true",
)

OAUTH_MERGE_ACCOUNTS_BY_EMAIL = PersistentConfig(
    "OAUTH_MERGE_ACCOUNTS_BY_EMAIL",
    "oauth.merge_accounts_by_email",
    os.environ.get("OAUTH_MERGE_ACCOUNTS_BY_EMAIL", "False").lower() == "true",
)

OAUTH_PROVIDERS = {}

GOOGLE_CLIENT_ID = PersistentConfig(
    "GOOGLE_CLIENT_ID",
    "oauth.google.client_id",
    os.environ.get("GOOGLE_CLIENT_ID", ""),
)

GOOGLE_CLIENT_SECRET = PersistentConfig(
    "GOOGLE_CLIENT_SECRET",
    "oauth.google.client_secret",
    os.environ.get("GOOGLE_CLIENT_SECRET", ""),
)

GOOGLE_OAUTH_SCOPE = PersistentConfig(
    "GOOGLE_OAUTH_SCOPE",
    "oauth.google.scope",
    os.environ.get("GOOGLE_OAUTH_SCOPE", "openid email profile"),
)

GOOGLE_REDIRECT_URI = PersistentConfig(
    "GOOGLE_REDIRECT_URI",
    "oauth.google.redirect_uri",
    os.environ.get("GOOGLE_REDIRECT_URI", ""),
)

MICROSOFT_CLIENT_ID = PersistentConfig(
    "MICROSOFT_CLIENT_ID",
    "oauth.microsoft.client_id",
    os.environ.get("MICROSOFT_CLIENT_ID", ""),
)

MICROSOFT_CLIENT_SECRET = PersistentConfig(
    "MICROSOFT_CLIENT_SECRET",
    "oauth.microsoft.client_secret",
    os.environ.get("MICROSOFT_CLIENT_SECRET", ""),
)

MICROSOFT_CLIENT_TENANT_ID = PersistentConfig(
    "MICROSOFT_CLIENT_TENANT_ID",
    "oauth.microsoft.tenant_id",
    os.environ.get("MICROSOFT_CLIENT_TENANT_ID", ""),
)

MICROSOFT_CLIENT_LOGIN_BASE_URL = PersistentConfig(
    "MICROSOFT_CLIENT_LOGIN_BASE_URL",
    "oauth.microsoft.login_base_url",
    os.environ.get(
        "MICROSOFT_CLIENT_LOGIN_BASE_URL", "https://login.microsoftonline.com"
    ),
)

MICROSOFT_CLIENT_PICTURE_URL = PersistentConfig(
    "MICROSOFT_CLIENT_PICTURE_URL",
    "oauth.microsoft.picture_url",
    os.environ.get(
        "MICROSOFT_CLIENT_PICTURE_URL",
        "https://graph.microsoft.com/v1.0/me/photo/$value",
    ),
)

MICROSOFT_OAUTH_SCOPE = PersistentConfig(
    "MICROSOFT_OAUTH_SCOPE",
    "oauth.microsoft.scope",
    os.environ.get("MICROSOFT_OAUTH_SCOPE", "openid email profile"),
)

MICROSOFT_REDIRECT_URI = PersistentConfig(
    "MICROSOFT_REDIRECT_URI",
    "oauth.microsoft.redirect_uri",
    os.environ.get("MICROSOFT_REDIRECT_URI", ""),
)

GITHUB_CLIENT_ID = PersistentConfig(
    "GITHUB_CLIENT_ID",
    "oauth.github.client_id",
    os.environ.get("GITHUB_CLIENT_ID", ""),
)

GITHUB_CLIENT_SECRET = PersistentConfig(
    "GITHUB_CLIENT_SECRET",
    "oauth.github.client_secret",
    os.environ.get("GITHUB_CLIENT_SECRET", ""),
)

GITHUB_CLIENT_SCOPE = PersistentConfig(
    "GITHUB_CLIENT_SCOPE",
    "oauth.github.scope",
    os.environ.get("GITHUB_CLIENT_SCOPE", "user:email"),
)

GITHUB_CLIENT_REDIRECT_URI = PersistentConfig(
    "GITHUB_CLIENT_REDIRECT_URI",
    "oauth.github.redirect_uri",
    os.environ.get("GITHUB_CLIENT_REDIRECT_URI", ""),
)

OAUTH_CLIENT_ID = PersistentConfig(
    "OAUTH_CLIENT_ID",
    "oauth.client_id",
    os.environ.get("OAUTH_CLIENT_ID", ""),
)

OAUTH_CLIENT_SECRET = PersistentConfig(
    "OAUTH_CLIENT_SECRET",
    "oauth.client_secret",
    os.environ.get("OAUTH_CLIENT_SECRET", ""),
)

OAUTH_CLIENT_SCOPE = PersistentConfig(
    "OAUTH_CLIENT_SCOPE",
    "oauth.scope",
    os.environ.get("OAUTH_CLIENT_SCOPE", "openid email profile"),
)

OAUTH_CLIENT_REDIRECT_URI = PersistentConfig(
    "OAUTH_CLIENT_REDIRECT_URI",
    "oauth.redirect_uri",
    os.environ.get("OAUTH_CLIENT_REDIRECT_URI", ""),
)

OAUTH_CLIENT_AUTHORIZATION_URL = PersistentConfig(
    "OAUTH_CLIENT_AUTHORIZATION_URL",
    "oauth.authorization_url",
    os.environ.get("OAUTH_CLIENT_AUTHORIZATION_URL", ""),
)

OAUTH_CLIENT_TOKEN_URL = PersistentConfig(
    "OAUTH_CLIENT_TOKEN_URL",
    "oauth.token_url",
    os.environ.get("OAUTH_CLIENT_TOKEN_URL", ""),
)

OAUTH_CLIENT_USERINFO_URL = PersistentConfig(
    "OAUTH_CLIENT_USERINFO_URL",
    "oauth.userinfo_url",
    os.environ.get("OAUTH_CLIENT_USERINFO_URL", ""),
)

OAUTH_CLIENT_USERNAME_ATTR = PersistentConfig(
    "OAUTH_CLIENT_USERNAME_ATTR",
    "oauth.username_attr",
    os.environ.get("OAUTH_CLIENT_USERNAME_ATTR", "email"),
)

OAUTH_CLIENT_EMAIL_ATTR = PersistentConfig(
    "OAUTH_CLIENT_EMAIL_ATTR",
    "oauth.email_attr",
    os.environ.get("OAUTH_CLIENT_EMAIL_ATTR", "email"),
)

OAUTH_CLIENT_NAME_ATTR = PersistentConfig(
    "OAUTH_CLIENT_NAME_ATTR",
    "oauth.name_attr",
    os.environ.get("OAUTH_CLIENT_NAME_ATTR", "name"),
)

OAUTH_CLIENT_PICTURE_ATTR = PersistentConfig(
    "OAUTH_CLIENT_PICTURE_ATTR",
    "oauth.picture_attr",
    os.environ.get("OAUTH_CLIENT_PICTURE_ATTR", "picture"),
)

# Continue with all other configuration variables...
# (This is a sample - you would continue with all the other config variables from the original file)

log.info("Windows-native configuration system initialized successfully") 