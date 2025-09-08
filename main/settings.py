import os
from pathlib import Path
from dotenv import load_dotenv
from decouple import config

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG setting - can be set via environment variable or command line
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes', 'on')

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    
    #my apps
    'accounts',
    'posts',
    'chat',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS configuration
# For now, allow all origins to fix CORS issues
# You can restrict this later when you deploy your frontend
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Additional CORS settings
CORS_PREFLIGHT_MAX_AGE = 86400
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Session configuration for cross-origin requests
# Use Lax and False for both development and production when frontend is HTTP
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Must be False for JavaScript access
SESSION_COOKIE_DOMAIN = None

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://horizonixsocialmediaappbackend-production.up.railway.app",
    # Add your frontend domain here when you deploy it
    "https://your-frontend-domain.vercel.app",
    "https://your-frontend-domain.netlify.app",
]

ROOT_URLCONF = 'main.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'main.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

if DEBUG:
    # Development: Use SQLite3
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Production: Use PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'railway',
            'USER': 'postgres',
            'PASSWORD': os.getenv('PG_PASSWORD', 'RDcBeitHJKGYPxkGemNXjnKYZCtwcGze'),
            'HOST': os.getenv('PG_HOST', 'tramway.proxy.rlwy.net'),
            'PORT': os.getenv('PG_PORT', '47308'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"


# Media files configuration based on DEBUG setting
# When DEBUG=False and CLOUDINARY_URL is provided, use Cloudinary
# Otherwise, use local media files for development

if not DEBUG:
    _cloudinary_url = config('CLOUDINARY_URL', default=None)
    if _cloudinary_url:
        # Configure Cloudinary storage for media when not in DEBUG and URL provided
        INSTALLED_APPS += [
            'cloudinary_storage',
            'cloudinary',
        ]
        os.environ.setdefault('CLOUDINARY_URL', _cloudinary_url)

        STORAGES = {
            'default': {
                'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
            },
            # Use WhiteNoise for compressed static files in production
            'staticfiles': {
                'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
            },
        }
    else:
        # Production without Cloudinary - use local media
        MEDIA_URL = '/media/'
        MEDIA_ROOT = BASE_DIR / 'media'
else:
    # Development: Use local media files
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# For now, let's use local media storage for both development and production
# to avoid Cloudinary issues. You can enable Cloudinary later when needed.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Email configuration
if DEBUG:
    # Development: Use console backend
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@horizonix.com'
else:
    # Production: Use SMTP backend
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@horizonix.com')

# Frontend base URL for building email verification links
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')