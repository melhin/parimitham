import os
from pathlib import Path

from configurations.values import PositiveIntegerValue, Value

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True')
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = 'parimitham.urls'
WSGI_APPLICATION = 'parimitham.wsgi.application'

INSTALLED_APPS = [
   'django.contrib.contenttypes',
   'django.contrib.auth',
   'django_tasks',
   'django_tasks.backends.database',
   'parimitham.core',
]

MIDDLEWARE = [
   'django.middleware.security.SecurityMiddleware',
   'django.middleware.common.CommonMiddleware',
   'django.middleware.csrf.CsrfViewMiddleware',
   'django.contrib.sessions.middleware.SessionMiddleware',
   'django.contrib.auth.middleware.AuthenticationMiddleware',
   'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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
TASKS = {
   'default': {'BACKEND': 'parimitham.core.interpreter_queue_backend.InterpreterQueueBackend'}
}

DB_HOST = Value(environ_prefix=None, environ_name="DB_HOST", default="localhost")
DB_NAME = Value(environ_prefix=None, environ_name="DB_NAME", default="parimitham")
DB_SCHEMA = Value(environ_prefix=None, environ_name="DB_SCHEMA", default="public")
DB_USER = Value(environ_prefix=None, environ_name="DB_USER", default="postgres")
DB_PASS = Value(environ_prefix=None, environ_name="DB_PASS", default="postgres")

DB_PORT = PositiveIntegerValue(
    environ_prefix=None, environ_name="DB_PORT", default=5432
)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "options": "-c search_path=" + DB_SCHEMA,
        },
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASS,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "TEST": {
            "NAME": "test_" + DB_NAME,
        },
    }
}


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "text",
            "stream": "ext://sys.stdout",
        }
    },
    "formatters": {
        "text": {
            "format": "%(asctime)s %(levelname)s %(thread)d %(process)d %(module)s %(name)s %(message)s",
        },
    },
}

LOGGING_CONFIG = None
