"""
Open WebUI DXMatrix Edition - Windows Native Session Middleware
Replaces Starlette's SessionMiddleware with SQLite-based session management
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Optional, Dict, Any
import uuid

from session_manager import get_session_manager

# Set up debug logger
logger = logging.getLogger("windows_session_middleware")
logger.setLevel(logging.DEBUG)

class WindowsSessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        secret_key: str,
        session_cookie: str = "oui-session",
        same_site: str = "lax",
        https_only: bool = False,
        max_age: int = 60 * 60 * 24 * 7,  # 1 week
    ):
        super().__init__(app)
        self.secret_key = secret_key
        self.session_cookie = session_cookie
        self.same_site = same_site
        self.https_only = https_only
        self.max_age = max_age
        self.session_mgr = get_session_manager()
        logger.debug(f"Windows Session Middleware initialized with cookie: {self.session_cookie}")

    async def dispatch(self, request: Request, call_next):
        # 1. Load session from cookie
        session_id = request.cookies.get(self.session_cookie)
        logger.debug(f"Incoming request: {request.url} | Session ID from cookie: {session_id}")
        session_data = {}
        if session_id:
            session_data = self.session_mgr.get_session(session_id) or {}
            logger.debug(f"Loaded session data: {session_data}")
        else:
            logger.debug("No session ID found in cookies. Starting new session.")

        # 2. Attach session dict to request.state
        request.state.session_id = session_id
        request.state.session_modified = False

        class SessionDict(dict):
            def __setitem__(self, key, value):
                logger.debug(f"Session set: {key} = {value}")
                super().__setitem__(key, value)
                request.state.session_modified = True
            def __delitem__(self, key):
                logger.debug(f"Session delete: {key}")
                super().__delitem__(key)
                request.state.session_modified = True
            def clear(self):
                logger.debug("Session clear")
                super().clear()
                request.state.session_modified = True

        request.state.session = SessionDict(session_data)

        # 3. Process request
        response = await call_next(request)

        # 4. Save session if modified
        if request.state.session_modified:
            logger.debug(f"Session modified. Saving session: {dict(request.state.session)}")
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.debug(f"Generated new session ID: {session_id}")
            self.session_mgr.update_session(session_id, dict(request.state.session))
            response.set_cookie(
                key=self.session_cookie,
                value=session_id,
                max_age=self.max_age,
                httponly=True,
                samesite=self.same_site,
                secure=self.https_only,
            )
            logger.debug(f"Set session cookie: {self.session_cookie} = {session_id}")
        else:
            logger.debug("Session not modified. No save needed.")

        return response 