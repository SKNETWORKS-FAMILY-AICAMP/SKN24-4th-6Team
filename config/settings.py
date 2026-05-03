import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일을 os.environ 에 로드 (파일 없으면 무시)
environ.Env.read_env(BASE_DIR / ".env")

# ================================================================
# 기본
# ================================================================
SECRET_KEY = os.environ.get(
  "DJANGO_SECRET_KEY", "django-insecure-dev-only-do-not-use-in-prod"
)  # .env: DJANGO_SECRET_KEY

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"  # .env: DJANGO_DEBUG

ALLOWED_HOSTS = [
  h.strip()
  for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
  if h.strip()
]  # .env: DJANGO_ALLOWED_HOSTS (콤마 구분)

# HTTPS 도메인에서 POST/PUT/DELETE 가 동작하려면 운영 도메인을 등록해야 함 (예: https://api.example.com)
CSRF_TRUSTED_ORIGINS = [
  o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]  # .env: DJANGO_CSRF_TRUSTED_ORIGINS (콤마 구분, scheme 포함)


# ================================================================
# 앱 목록
# ================================================================
INSTALLED_APPS = [
  "django.contrib.admin",
  "django.contrib.auth",
  "django.contrib.contenttypes",
  "django.contrib.sessions",
  "django.contrib.messages",
  "django.contrib.staticfiles",
  "rest_framework",
  "whitenoise.runserver_nostatic",
  "core",
  "accounts",
  "health",
  "chat",
  "contract",
]


# ================================================================
# 미들웨어
# ================================================================
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

TEMPLATES = [
  {
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
      "context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
      ],
    },
  },
]


# ================================================================
# Database
# ================================================================
# [로컬] SQLite — 별도 설치 없이 즉시 실행 가능
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#         'TEST': {'NAME': ':memory:'},  # pytest: 인메모리 DB 사용
#     }
# }

# [운영] PostgreSQL — 운영 환경에서 아래 주석 해제 후 위 SQLite 블록 주석처리
DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("DB_NAME", "aigo_web"),  # .env: DB_NAME
    "USER": os.environ.get("DB_USER", "postgres"),  # .env: DB_USER
    "PASSWORD": os.environ.get("DB_PASSWORD", ""),  # .env: DB_PASSWORD
    "HOST": os.environ.get("DB_HOST", "localhost"),  # .env: DB_HOST
    "PORT": os.environ.get("DB_PORT", "5432"),  # .env: DB_PORT
  }
}


# ================================================================
# 커스텀 User 모델
# AbstractBaseUser 상속 → 이 설정 없으면 Django가 기본 User 참조
# ================================================================
AUTH_USER_MODEL = "core.User"

# LoginRequiredMixin 미인증 리다이렉트 → 랜딩(/login/) 으로
# /login/ 라우트는 index.html 을 렌더하고 모달로 로그인 처리됨
LOGIN_URL = "/login/"

AUTH_PASSWORD_VALIDATORS = [
  {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
  {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
  {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
  {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ================================================================
# DRF
# ================================================================
REST_FRAMEWORK = {
  "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.SessionAuthentication",),
  "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}


# ================================================================
# 이메일
# ================================================================
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = f"아이고청년 <{os.environ.get('EMAIL_HOST_USER', '')}>"


# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# DEBUG=True면 터미널에 출력, 운영은 Gmail SMTP 사용
if DEBUG:
  EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
  EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


# ================================================================
# Static / Media
# ================================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").is_dir() else []

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

STORAGES = {
  "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
  "staticfiles": {
    # 운영: 해시 + gzip/brotli 으로 캐시 무효화 + 트래픽 절감
    # 개발: 단순 storage
    "BACKEND": (
      "django.contrib.staticfiles.storage.StaticFilesStorage"
      if DEBUG
      else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    ),
  },
}


# ================================================================
# 외부 서비스
# ================================================================
AIGO_AI_BASE_URL = os.environ.get(
  "AIGO_AI_BASE_URL", "http://localhost:8001"
)  # .env: AIGO_AI_BASE_URL
AIGO_AI_INTERNAL_API_KEY = os.environ.get("AIGO_AI_INTERNAL_API_KEY", "")
AIGO_AI_REQUEST_TIMEOUT = float(os.environ.get("AIGO_AI_REQUEST_TIMEOUT", "120"))


# ================================================================
# 기타
# ================================================================
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ================================================================
# 보안 / HTTPS
# nginx 가 SSL 종단(443) 이고 gunicorn 으로 HTTP 프록시되는 구조 가정
# ================================================================
# nginx 가 X-Forwarded-Proto: https 헤더를 넣어주면 Django 가 HTTPS 로 인식
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# 운영(DEBUG=False)에서만 secure cookie. 로컬 HTTP 개발 시에는 꺼짐
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# HTTP -> HTTPS 강제 리다이렉트. 인증서 발급 전엔 False 유지 (chicken-and-egg 방지)
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "False") == "True"

# HSTS (인증서 안정 운영 후 활성화 권장. 0 = 비활성)
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0


# ================================================================
# 로깅
# systemd journal / CloudWatch 로 stdout/stderr 수집되도록 콘솔 핸들러만 사용
# ================================================================
_LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO")

LOGGING = {
  "version": 1,
  "disable_existing_loggers": False,
  "formatters": {
    "standard": {
      "format": "[{asctime}] {levelname} {name}: {message}",
      "style": "{",
    },
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "formatter": "standard",
    },
  },
  "root": {
    "handlers": ["console"],
    "level": _LOG_LEVEL,
  },
  "loggers": {
    "django": {
      "handlers": ["console"],
      "level": _LOG_LEVEL,
      "propagate": False,
    },
    "django.request": {
      "handlers": ["console"],
      "level": "WARNING",
      "propagate": False,
    },
  },
}
