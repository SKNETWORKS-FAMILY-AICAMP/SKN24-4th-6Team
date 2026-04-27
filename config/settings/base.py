"""Shared settings. Loaded by dev/prod/test via `from .base import *`."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# Read .env files in order of preference. First match wins for any given key.
# .env.local takes precedence in dev; .env.prod is loaded only when present.
for candidate in (".env.local", ".env.prod", ".env"):
  env_path = BASE_DIR / candidate
  if env_path.is_file():
    environ.Env.read_env(env_path)

# ── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = env(
  "DJANGO_SECRET_KEY",
  default="django-insecure-dev-only-do-not-use-in-prod",
)
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# ── Apps ────────────────────────────────────────────────────────────────────
DJANGO_APPS = [
  "django.contrib.admin",
  "django.contrib.auth",
  "django.contrib.contenttypes",
  "django.contrib.sessions",
  "django.contrib.messages",
  "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
  "rest_framework",
  "rest_framework_simplejwt.token_blacklist",
]

LOCAL_APPS = [
  "accounts",
  "health",
  "chat",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware (whitenoise must sit immediately after SecurityMiddleware) ───
MIDDLEWARE = [
  "django.middleware.security.SecurityMiddleware",
  "whitenoise.middleware.WhiteNoiseMiddleware",
  "django.contrib.sessions.middleware.SessionMiddleware",
  "django.middleware.common.CommonMiddleware",
  "django.middleware.csrf.CsrfViewMiddleware",
  "django.contrib.auth.middleware.AuthenticationMiddleware",
  "django.contrib.messages.middleware.MessageMiddleware",
  "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── Templates ───────────────────────────────────────────────────────────────
TEMPLATES = [
  {
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
      "context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
      ],
    },
  },
]

# ── Database ────────────────────────────────────────────────────────────────
# DATABASE_URL must use the psycopg 3 scheme: postgresql+psycopg://...
# Local dev sqlite fallback only — prod overrides this in prod.py without a default.
DATABASES = {
  "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

# ── Auth ────────────────────────────────────────────────────────────────────
# Locked early so AUTH_USER_MODEL is in the very first migration.
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
  {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
  {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
  {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
  {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── i18n ────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = env("DJANGO_LANGUAGE_CODE", default="ko-kr")
TIME_ZONE = env("DJANGO_TIME_ZONE", default="Asia/Seoul")
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

# ── Static / media ──────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / env("DJANGO_STATIC_ROOT", default="staticfiles")
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").is_dir() else []

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# Whitenoise: compressed + manifest in prod; dev.py loosens this.
STORAGES = {
  "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
  "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# ── Defaults ────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── DRF ─────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
  "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
  "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# ── JWT (simplejwt) ─────────────────────────────────────────────────────────
# Tokens are signed with DJANGO_JWT_SIGNING_KEY when set, else fall back to
# SECRET_KEY. Rotating + blacklisting refresh tokens makes logout work via
# the /api/auth/token/blacklist endpoint.
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
  "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
  "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
  "ROTATE_REFRESH_TOKENS": True,
  "BLACKLIST_AFTER_ROTATION": True,
  "SIGNING_KEY": env("DJANGO_JWT_SIGNING_KEY", default=SECRET_KEY),
  "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── External services ───────────────────────────────────────────────────────
# aigo-ai (FastAPI RAG service) base URL — chat.services.ask_aigo_ai posts here.
AIGO_AI_BASE_URL = env("AIGO_AI_BASE_URL", default="http://localhost:8000")
