"""Production settings — strict secrets, secure cookies, no DB fallback."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# Required in prod: raise if missing rather than using base.py's insecure default.
SECRET_KEY = env("DJANGO_SECRET_KEY")

# Required in prod: no SQLite fallback.
DATABASES = {"default": env.db("DATABASE_URL")}

# HTTPS / cookies.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
