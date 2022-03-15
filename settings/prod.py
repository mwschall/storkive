import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)

# cwd is settings. determine project path
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


# Security
# https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

try:
    SECRET_KEY = os.environ['SECRET_KEY']
    with open(SECRET_KEY, 'r') as skf:
        SECRET_KEY = skf.readline().strip()
except KeyError:
    logger.warning('Using a random SECRET_KEY. This will not persist across restarts or between workers.')
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = 'django-temporary-' + get_random_secret_key()
except FileNotFoundError:
    pass

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
