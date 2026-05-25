"""
Django settings for vinylsite project — «Коллекция винила».
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in ('1', 'true', 'yes', 'on')


# На Timeweb задан DJANGO_SECRET_KEY — по умолчанию не показывать страницы с DEBUG.
DEBUG = _env_bool('DJANGO_DEBUG', not os.environ.get('DJANGO_SECRET_KEY'))

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-&50z88s_9*e-zzy+w46l5e7850-(rli(r2eu1(_j2po$!5p@u4',
)

_allowed_raw = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _allowed_raw.split(',') if h.strip()] or ['*']


def _build_csrf_trusted_origins():
    origins = []
    seen = set()

    def add(origin: str):
        origin = origin.strip().rstrip('/')
        if origin and origin not in seen:
            seen.add(origin)
            origins.append(origin)

    for item in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(','):
        add(item)

    add(os.environ.get('DJANGO_SITE_URL', '').strip().rstrip('/'))

    for host in ALLOWED_HOSTS:
        if not host or host == '*':
            continue
        if host.startswith('.'):
            continue
        add(f'https://{host}')
        if DEBUG:
            add(f'http://{host}')

    # Timeweb App Platform: *.twc1.net (Django поддерживает wildcard в CSRF_TRUSTED_ORIGINS)
    if _env_bool('DJANGO_TRUST_TIMEWEB_CSRF', True):
        add('https://*.twc1.net')

    return origins


CSRF_TRUSTED_ORIGINS = _build_csrf_trusted_origins()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'collection',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'collection.csrf_middleware.VinylCsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'collection.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vinylsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'collection.context_processors.collection_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'vinylsite.wsgi.application'

if os.environ.get('DATABASE_PATH'):
    _db_name = os.environ['DATABASE_PATH']
elif not DEBUG:
    _db_name = '/tmp/vinyl_collection.sqlite3'
else:
    _db_name = str(BASE_DIR / 'db.sqlite3')

try:
    Path(_db_name).parent.mkdir(parents=True, exist_ok=True)
except OSError:
    _db_name = '/tmp/vinyl_collection.sqlite3'
    Path(_db_name).parent.mkdir(parents=True, exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _db_name,
        'OPTIONS': {
            'timeout': 60,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'collection' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# На Timeweb runtime-контейнер может не содержать staticfiles после сборки — отдаём из исходников.
WHITENOISE_USE_FINDERS = _env_bool('WHITENOISE_USE_FINDERS', not DEBUG)

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

MEDIA_URL = 'media/'

if os.environ.get('MEDIA_ROOT_PATH'):
    MEDIA_ROOT = Path(os.environ['MEDIA_ROOT_PATH'])
elif not DEBUG:
    # /app/media на Timeweb часто read-only — загрузки и поворот фото в /tmp
    MEDIA_ROOT = Path('/tmp/vinyl_media')
else:
    MEDIA_ROOT = Path(BASE_DIR / 'media')

try:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
except OSError:
    MEDIA_ROOT = Path('/tmp/vinyl_media')
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'album_list'
LOGOUT_REDIRECT_URL = 'login'

# Timeweb/nginx: без этого request.is_secure()=False при HTTPS → CSRF отклоняет Origin.
if _env_bool('DJANGO_BEHIND_PROXY', True):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

if not DEBUG:
    # Сессии в cookie — не нужна таблица django_session на БД в /tmp.
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
    _secure_cookies = _env_bool('DJANGO_SECURE_COOKIES', False)
    SESSION_COOKIE_SECURE = _secure_cookies
    CSRF_COOKIE_SECURE = _secure_cookies
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
