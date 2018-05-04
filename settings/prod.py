import os

# cwd is settings. determine project path
cwd = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = cwd[:-9]  # chop off "settings/"

# Security
# https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

SECRET_KEY = os.environ['SECRET_KEY']

CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'


# Application definition

INSTALLED_APPS = [
    'storages',
]


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'storkive',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
