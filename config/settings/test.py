"""Test settings — in-memory sqlite, fast hasher, no whitenoise manifest."""

from .base import *  # noqa: F401,F403
from .base import STORAGES

DEBUG = False

DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
  },
}

# Speed up password ops in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Plain static storage so collectstatic isn't required for tests.
STORAGES["staticfiles"] = {
  "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
