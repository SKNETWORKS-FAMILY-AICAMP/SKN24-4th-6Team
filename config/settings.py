import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일을 os.environ 에 로드 (파일 없으면 무시)
environ.Env.read_env(BASE_DIR / '.env')

# ================================================================
# 기본
# ================================================================
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-only-do-not-use-in-prod')  # .env: DJANGO_SECRET_KEY

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')  # .env: ALLOWED_HOSTS


# ================================================================
# 앱 목록
# ================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'whitenoise.runserver_nostatic',
    'core',
    'accounts',
    'health',
    'chat',
    'contract',
]


# ================================================================
# 미들웨어
# ================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
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
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'aigo_web'),        # .env: DB_NAME
        'USER': os.environ.get('DB_USER', 'postgres'),         # .env: DB_USER
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),         # .env: DB_PASSWORD
        'HOST': os.environ.get('DB_HOST', 'localhost'),        # .env: DB_HOST
        'PORT': os.environ.get('DB_PORT', '5432'),             # .env: DB_PORT
    }
}


# ================================================================
# 커스텀 User 모델
# AbstractBaseUser 상속 → 이 설정 없으면 Django가 기본 User 참조
# ================================================================
AUTH_USER_MODEL = 'core.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ================================================================
# DRF
# ================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


# ================================================================
# 이메일
# 설계서 SCR-USER-004 항목 2: 회원가입 인증코드 발송
# 설계서 SCR-USER-005 항목 2: 비밀번호 재설정 인증코드 발송
# ================================================================
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = f'아이고청년 <{os.environ.get("EMAIL_HOST_USER", "")}>'

# DEBUG=True면 터미널에 출력, 운영은 Gmail SMTP 사용
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


# ================================================================
# Static / Media
# ================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').is_dir() else []

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


# ================================================================
# 외부 서비스
# ================================================================
AIGO_AI_BASE_URL = os.environ.get('AIGO_AI_BASE_URL', 'http://localhost:8001')  # .env: AIGO_AI_BASE_URL


# ================================================================
# 기타
# ================================================================
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
