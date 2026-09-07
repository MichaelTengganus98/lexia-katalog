"""
Django settings for katalog project.

Configuration is environment-driven so the same code runs locally, on
staging, and on production. Nothing needs editing to deploy — set the
DJANGO_* / DATABASE_URL environment variables (in cPanel: Setup Python App
-> Environment variables, or a .env file next to manage.py).

See .env.example for the full list and DEPLOY_STAGING.md for the steps.
"""

import os

import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- tiny .env loader (no dependency) --------------------------------------
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _fh:
        for _line in _fh:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return str(env(key, str(default))).strip().lower() in ("1", "true", "yes", "on")


def env_list(key, default=""):
    return [x.strip() for x in env(key, default).split(",") if x.strip()]


# local | staging | production
DJANGO_ENV = env("DJANGO_ENV", "local")
IS_LOCAL = DJANGO_ENV == "local"
IS_PROD = DJANGO_ENV == "production"

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    ")qaq!872vp7*wq3$(wf00f1l7qtsnkt1=bm5hqxx--vzp^sfb%",  # dev fallback only
)

DEBUG = env_bool("DJANGO_DEBUG", IS_LOCAL)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"] if DEBUG else ["www.lexia.co.id", "lexia.co.id"]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'homepage',
    'about',
    'item',
    'search',
    'page',
    'seo',
    'blog',
    'panel',
    'django_cleanup',
    'sorl.thumbnail',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'katalog.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'page.context_navbar.menu_mesin',
                'seo.context_processors.seo',
            ],
        },
    },
]

WSGI_APPLICATION = 'katalog.wsgi.application'


# Database — DATABASE_URL wins, otherwise local sqlite file
# e.g.  DATABASE_URL=mysql://lexiacoi_staging:PASSWORD@localhost/lexiacoi_staging
DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3"),
        conn_max_age=600,
    )
}
if DATABASES["default"].get("ENGINE") == "django.db.backends.mysql":
    _opts = DATABASES["default"].setdefault("OPTIONS", {})
    _opts["charset"] = "utf8mb4"
    _opts.setdefault("sql_mode", "STRICT_TRANS_TABLES")


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static & media
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "assets")]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATIC_ROOT = env("DJANGO_STATIC_ROOT", os.path.join(PROJECT_ROOT, "static"))
MEDIA_ROOT = env("DJANGO_MEDIA_ROOT", os.path.join(BASE_DIR, "media"))

FILE_UPLOAD_PERMISSIONS = 0o644


# Cache — memcached when a location is provided, else in-process
_memcached = env("DJANGO_MEMCACHED_LOCATION")
if _memcached:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': _memcached,
        }
    }


# Security — on whenever not DEBUG, unless explicitly overridden
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
_ssl = env_bool("DJANGO_SECURE_SSL", not DEBUG)
SECURE_SSL_REDIRECT = _ssl
SESSION_COOKIE_SECURE = _ssl
CSRF_COOKIE_SECURE = _ssl
if _ssl:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Redirect apex -> www only for the production domain (never a staging subdomain)
PREPEND_WWW = env_bool("DJANGO_PREPEND_WWW", IS_PROD)

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")


# sorl-thumbnail: emit WebP (smaller than JPEG/PNG, ~98% browser support)
THUMBNAIL_FORMAT = 'WEBP'
THUMBNAIL_QUALITY = 82
