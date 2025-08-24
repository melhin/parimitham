from pathlib import Path
import os

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

DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.sqlite3',
       'NAME': BASE_DIR / 'db.sqlite3',
       'OPTIONS': {
           'init_command': (
               'pragma journal_mode = WAL; pragma synchronous = normal; '
               'pragma temp_store = memory; pragma mmap_size = 30000000000;'
           )
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
