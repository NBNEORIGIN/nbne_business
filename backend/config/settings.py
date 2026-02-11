import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-rev2-dev-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# --- Module feature flags ---------------------------------------------------
PAYMENTS_MODULE_ENABLED = os.environ.get('PAYMENTS_MODULE_ENABLED', 'True') == 'True'
TENANTS_MODULE_ENABLED = os.environ.get('TENANTS_MODULE_ENABLED', 'True') == 'True'
BOOKINGS_MODULE_ENABLED = os.environ.get('BOOKINGS_MODULE_ENABLED', 'True') == 'True'
STAFF_MODULE_ENABLED = os.environ.get('STAFF_MODULE_ENABLED', 'True') == 'True'
COMMS_MODULE_ENABLED = os.environ.get('COMMS_MODULE_ENABLED', 'True') == 'True'
COMPLIANCE_MODULE_ENABLED = os.environ.get('COMPLIANCE_MODULE_ENABLED', 'True') == 'True'
DOCUMENTS_MODULE_ENABLED = os.environ.get('DOCUMENTS_MODULE_ENABLED', 'True') == 'True'
CRM_MODULE_ENABLED = os.environ.get('CRM_MODULE_ENABLED', 'True') == 'True'
ANALYTICS_MODULE_ENABLED = os.environ.get('ANALYTICS_MODULE_ENABLED', 'True') == 'True'

# --- Installed apps ----------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    # Core rev_2 apps (always enabled)
    'accounts',
    'auditlog',
]

# Conditionally register optional modules
if TENANTS_MODULE_ENABLED:
    INSTALLED_APPS.append('tenants')
if BOOKINGS_MODULE_ENABLED:
    INSTALLED_APPS.append('bookings')
if PAYMENTS_MODULE_ENABLED:
    INSTALLED_APPS.append('payments')
if STAFF_MODULE_ENABLED:
    INSTALLED_APPS.append('staff')
if COMMS_MODULE_ENABLED:
    INSTALLED_APPS.append('comms')
if COMPLIANCE_MODULE_ENABLED:
    INSTALLED_APPS.append('compliance')
if DOCUMENTS_MODULE_ENABLED:
    INSTALLED_APPS.append('documents')
if CRM_MODULE_ENABLED:
    INSTALLED_APPS.append('crm')
if ANALYTICS_MODULE_ENABLED:
    INSTALLED_APPS.append('analytics')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auditlog.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'

# --- Database ----------------------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

# --- Custom User Model -------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Django REST Framework ---------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# --- Simple JWT --------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'accounts.serializers.CustomTokenObtainPairSerializer',
}

# --- Stripe / Payments settings ----------------------------------------------
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
PAYMENTS_ENABLED = os.environ.get('PAYMENTS_ENABLED', 'True') == 'True'
DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'GBP')
PAYMENTS_WEBHOOK_CALLBACK_URL = os.environ.get('PAYMENTS_WEBHOOK_CALLBACK_URL', '')

# --- Email ------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.ionos.co.uk')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@nbnesigns.co.uk')

# --- CORS / CSRF ------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:3002').split(',')
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3002,https://nbne-business-mind-department.vercel.app').split(',')
CORS_ALLOW_CREDENTIALS = True
