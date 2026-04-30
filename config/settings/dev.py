"""Development settings — DEBUG on, relaxed static storage."""

from .base import *  # noqa: F401,F403
from .base import STORAGES

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Plain static storage — no manifest fingerprinting in dev (faster reloads).
STORAGES["staticfiles"] = {
  "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}

# Email to console.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
