"""
Django settings for elococo project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import decimal
import json
from decimal import Decimal
# SECURITY WARNING: don't run with debug turned on in production!
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
secrets = json.load(open(BASE_DIR / 'elococo' / 'secrets.json'))

DEBUG = True

if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn="https://cffd7602ac8945a89c05f9b386fe39ea@o267463.ingest.sentry.io/5810051",
        integrations=[DjangoIntegration()],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this dict_ in production.
        traces_sample_rate=1.0,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )

import psycopg2
import stripe

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secrets['secret_key']

ALLOWED_HOSTS = secrets['allowed_hosts']

# Application definition

INSTALLED_APPS = [
    'sale.apps.SaleConfig',
    'catalogue.apps.CatalogueConfig',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'treebeard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'sale.middlewares.BookingMiddleware'
]

ROOT_URLCONF = 'elococo.urls'

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
                'elococo.template_base_processor.template_base_processor'
            ],
        },
    },
]

WSGI_APPLICATION = 'elococo.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {}

if DEBUG:
    DATABASES.update({'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'elococo.db',  # This is where you put the name of the db file.
        # If one doesn't exist, it will be created at migration time.
    }})
else:
    DATABASES.update({'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': secrets["db"]["name"],
        'USER': secrets["db"]["user"],
        'PASSWORD': secrets["db"]["pwd"],
        'HOST': secrets["db"]["host"],
        'PORT': secrets["db"]["port"],
    },
        'OPTIONS': {
            'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE,
        }
    })

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_ROOT = BASE_DIR / "var/www/static/"
STATIC_URL = '/static/'
STATICFILES_DIRS = []

for directory in secrets["STATICFILES_DIRS"]:
    STATICFILES_DIRS.append(BASE_DIR / directory)

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# UPLOAD FIles
MEDIA_ROOT = BASE_DIR / "var/www/media/"
MEDIA_URL = '/media/'

# Website title
WEBSITE_TITLE = secrets["WEBSITE_TITLE"]

# MESSAGES
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

stripe.api_key = secrets["stripe"]["private_key"]
STRIPE_PUBLIC_KEY = secrets["stripe"]["public_key"]

EMAIL_USE_TLS = True
EMAIL_HOST = secrets["EMAIL_HOST"]
EMAIL_HOST_USER = secrets["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = secrets["EMAIL_HOST_PASSWORD"]
EMAIL_PORT = 587

# SHOP setting DON'T CHANGE
BOOKING_SESSION_KEY = "ordered_instance_pk"
BOOKING_SESSION_FILL_DELIVERY = "ordered_is_filled_delivery"
BOOKING_SESSION_FILL_KEY = "ordered_is_filled"
BOOKING_SESSION_FILL_2_KEY = "ordered_is_filled_next"
ORDERED_INSTANCE_KEY = "ordered_instance_key"

TIME_ORDERED_LIFE_MINUTES = 45
TIME_ORDERED_CLOSE_PAYMENT_TIME_BEFORE_END = 15
ORDER_SECRET_LENGTH = 30
PROMO_SECRET_LENGTH = 15

BASKET_SESSION_KEY = "basket"
PROMO_SESSION_KEY = "promo"
BASKET_MAX_QUANTITY_PER_FORM = 3
MAX_BASKET_PRODUCT = 8
PRODUCT_INSTANCE_KEY = "product_instance"

TVA_PERCENT = Decimal(20.)
BACK_TWO_PLACES = Decimal(10) ** -2
TVA = Decimal(120) * BACK_TWO_PLACES

CSRF_COOKIE_SECURE = True
STRIPE_WEBHOOK = secrets["stripe"]["webhook"]

DELIVERY_ORDINARY = Decimal(5.99)
DELIVERY_SPEED = Decimal(7.99)
DELIVERY_FREE_GT = Decimal(65.)
