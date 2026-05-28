"""SSO authenticator for the capstone hub — no login form.

The app (LMS) mints a short-lived JWT for a logged-in student and sends them to
    https://lab.bytek.tech/hub/lab-login?token=<jwt>
The token is HS256-signed with LAB_LAUNCH_SECRET (shared only between the LMS and this hub) and
carries {email, exp, aud}. This handler validates it and logs the student in, creating the user
on first visit. Username = a docker-safe slug of the email.
"""
import os
import re

import jwt
from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler
from jupyterhub.utils import url_path_join
from tornado import web

SECRET = os.environ.get("LAB_LAUNCH_SECRET", "")
AUDIENCE = os.environ.get("LAB_TOKEN_AUDIENCE", "lab")


def username_from_email(email: str) -> str:
    """email -> a username safe for JupyterHub + Docker volume/container names."""
    return re.sub(r"[^a-z0-9._-]", "-", (email or "").strip().lower()).strip("-") or "user"


class LabLoginHandler(BaseHandler):
    async def get(self):
        token = self.get_argument("token", "")
        if not SECRET:
            raise web.HTTPError(500, "LAB_LAUNCH_SECRET not configured")
        if not token:
            raise web.HTTPError(403, "missing launch token")
        try:
            claims = jwt.decode(token, SECRET, algorithms=["HS256"], audience=AUDIENCE)
        except jwt.PyJWTError:
            raise web.HTTPError(403, "invalid or expired launch token")
        email = (claims.get("email") or "").strip().lower()
        if not email:
            raise web.HTTPError(403, "launch token missing email")
        username = username_from_email(email)
        user = self.user_from_username(username)
        self.set_login_cookie(user)
        self.redirect(self.get_next_url(user, default=url_path_join(self.hub.base_url, "home")))


class LabAuthenticator(Authenticator):
    """Token hand-off SSO. Interactive login is disabled; identity comes from the launch token."""

    # Send anyone hitting /hub/login straight to the launch handler (no "Sign in" page).
    auto_login = True

    def get_handlers(self, app):
        return [("/lab-login", LabLoginHandler)]

    def login_url(self, base_url):
        return url_path_join(base_url, "lab-login")

    async def authenticate(self, handler, data):
        return None  # not used — the handler logs the user in directly
