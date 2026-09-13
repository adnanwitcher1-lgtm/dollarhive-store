"""
Django settings for the dollarhive project.

DollarHive — "Smart Deals. More Savings."
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Loads a local .env file if present (for local development only —
# Render provides real env vars directly, no .env file needed there).
load_dotenv(BASE_DIR / '.env')

# ----------------------------------------------------------------------
# Core / security
# ----------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'dev-only-secret-key-change-me-before-deploying'
)

# DEBUG defaults to False. Set DJANGO_DEBUG=True in a local .env for
# development only — never enable this in production.
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# Comma-separated list via env, e.g. "dollarhive.onrender.com,dollarhive.com"
_allowed = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()] or ['*']

# Needed so Render's HTTPS domain is trusted for POST forms (checkout, admin login).
_csrf_origins = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

# ----------------------------------------------------------------------
# Applications
# ----------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # DollarHive storefront app
    'store',
]

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

ROOT_URLCONF = 'dollarhive.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Project-level templates dir is optional; app templates are
        # auto-discovered from store/templates/ because APP_DIRS is True.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Makes {{ CART_ITEM_COUNT }} available on every page
                # (see store/context_processors.py) for the header badge.
                'store.context_processors.cart_item_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'dollarhive.wsgi.application'

# ----------------------------------------------------------------------
# Database — SQLite for local dev. If DATABASE_URL is set (Render's
# Postgres add-on sets this automatically), use that instead, because
# Render's own filesystem is wiped on every redeploy — SQLite data
# would not survive there.
# ----------------------------------------------------------------------
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# ----------------------------------------------------------------------
# Password validation
# ----------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------------------------------------------------------------
# Internationalization
# ----------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------------------------
# Static & media files
# ----------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'store' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------------------------------------------------------------
# Email settings — customer & merchant order notifications
# ----------------------------------------------------------------------
# 👉 Set these via environment variables (.env locally, dashboard env
#    vars on Render) — never hardcode real credentials here.
#    EMAIL_HOST_USER: your Gmail address
#    EMAIL_HOST_PASSWORD: a Gmail "App Password" (NOT your normal login
#    password). Get one here (after turning on 2-Step Verification):
#    https://myaccount.google.com/apppasswords
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 👉 The inbox that should receive "new order" alerts.
MERCHANT_EMAIL = os.environ.get('MERCHANT_EMAIL', EMAIL_HOST_USER)

# ----------------------------------------------------------------------
# WhatsApp notification settings (Twilio WhatsApp Business API)
# ----------------------------------------------------------------------
# Create a free Twilio account, enable the WhatsApp Sandbox (or a
# verified WhatsApp Business sender), and fill these in via
# environment variables. See store/notifications.py for usage.
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')  # Twilio sandbox number
MERCHANT_WHATSAPP_NUMBER = os.environ.get('MERCHANT_WHATSAPP_NUMBER', 'whatsapp:+10000000000')

# If True, notification failures are swallowed & logged instead of
# breaking checkout for the customer. Recommended: True in production.
NOTIFICATIONS_FAIL_SILENTLY = os.environ.get('NOTIFICATIONS_FAIL_SILENTLY', 'True') == 'True'

LOGIN_REDIRECT_URL = 'store:home'
LOGOUT_REDIRECT_URL = 'store:home'