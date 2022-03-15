import os
from pathlib import Path

from django.core.files.storage import FileSystemStorage

# cwd is settings. determine project path
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-rep^#%+j%0-ce8fp6j#$tqq9%ztn@x$=w^_x4rtbg2=&+ssijd'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

# SECURITY WARNING: this is super extra not-safe
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]


# Logging
# https://docs.djangoproject.com/en/dev/topics/logging/

LOGGING = {
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/


class OverwritingFSStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        # NOTE: this is all kinds of unsafe
        if os.path.exists(self.path(name)):
            os.remove(self.path(name))
        return name


DEFAULT_FILE_STORAGE = 'settings.dev.OverwritingFSStorage'
MEDIA_ROOT = BASE_DIR / '_data'
STATIC_ROOT = BASE_DIR / 'static'
