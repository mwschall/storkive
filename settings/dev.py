import os

# cwd is settings. determine project path
from django.core.files.storage import FileSystemStorage

cwd = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = cwd[:-9]  # chop off "settings/"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'rep^#%+j%0-ce8fp6j#$tqq9%ztn@x$=w^_x4rtbg2=&+ssijd'

DEBUG = True
TEMPLATE_DEBUG = DEBUG


# Application definition

INSTALLED_APPS = [
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
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
MEDIA_ROOT = os.path.join(BASE_DIR, '_data')
