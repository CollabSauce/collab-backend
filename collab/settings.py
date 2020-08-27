"""
Django settings for collab project.

Generated by 'django-admin startproject' using Django 3.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from corsheaders.defaults import default_headers

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '87r&i3cwg$ky)s!zvq(ruj#a24r6ly5rhbs!=#8(^*=1-6^kv('

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get("DEBUG", default=0))

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(" ")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',  # for django-allauth (for dj-rest-auth registration)
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # collab apps
    'collab_app.apps.CollabAppConfig',

    # 3rd party apps
    'allauth',  # for dj-rest-auth registration
    'allauth.account',  # for dj-rest-auth registration
    # required if we want to delete users https://github.com/pennersr/django-allauth/issues/1975#issuecomment-384075169
    'allauth.socialaccount',
    'corsheaders',
    'dynamic_rest',
    'rest_framework',
    'rest_framework.authtoken',  # for dj_rest_auth
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'djcelery_email',
    'django_extensions',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Debug ToolBar leaks memory by way of storing lots of information about all requests in memory. Forever.
# Never turn this on in production.
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

ROOT_URLCONF = 'collab.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR + '/templates/', BASE_DIR + '/collab_app/auth/templates/'
        ],
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

WSGI_APPLICATION = 'collab.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "PORT": os.environ.get("POSTGRES_PORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

# custom user model
AUTH_USER_MODEL = 'collab_app.User'

# For djang-allauth (for dj-rest-auth)
SITE_ID = 1
ACCOUNT_PRESERVE_USERNAME_CASING = False  # ignore casing on username
ACCOUNT_EMAIL_SUBJECT_PREFIX = ''  # no prefix on signup email header. i.e. no `[App_Name] `
ACCOUNT_ADAPTER = 'collab_app.auth.adapters.AuthAccountAdapter'  # overwrite a method for email vars
ACCOUNT_EMAIL_REQUIRED = True  # we are logging in/signing up through email, so this needs to be True
ACCOUNT_USERNAME_REQUIRED = False  # username not required
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # we login/signup through email


# For dj-rest-auth
# REST_USE_JWT = True  # to use json web tokens
OLD_PASSWORD_FIELD_ENABLED = True  # old_password_validation on password change
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', '')  # not in docs, but specifies the "from" field in emails

# for django-rest-auth custom serializers (for custom templates)
REST_AUTH_SERIALIZERS = {
    'PASSWORD_RESET_SERIALIZER': 'collab_app.auth.serializers.PasswordResetSerializer',
}

# Extra Django Rest Framework settings.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}

# for browseable api, redirect to /api
LOGIN_REDIRECT_URL = '/api'

# email config
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
# uncomment if want to print to console
CELERY_EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# CELERY_EMAIL_BACKEND = os.environ.get('CELERY_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

# Celery
CELERY_BROKER_URL = os.environ.get('CLOUDAMQP_URL', '')
CELERY_BROKER_POOL_LIMIT = 1  # for now on free cloudamqp tier (heroku) (can increase later if needed)

# CORS
# TODO(BRANDON) Fix for dev/stage/prod
CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    'custom-resource',  # for js-data on frontend :/
]