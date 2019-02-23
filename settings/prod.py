import os

# cwd is settings. determine project path
cwd = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = cwd[:-9]  # chop off "settings/"


# Security
# https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

try:
    SECRET_KEY = os.environ['SECRET_KEY']
except KeyError:
    import random
    SECRET_KEY = ''.join([
        random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
        for i in range(50)
    ])

CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'


# SECURITY WARNING: Deployed via docker-compose.prod.yaml and configured with
# a proper traefik.frontend.rule label, this can be left as-is in production.
# If your deployment differs, make sure to set the appropriate host here.
# See https://docs.djangoproject.com/en/dev/ref/settings/
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'storages',
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/storkive/media/')
