from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment

from library.templatetags.library_extras import story_count, long_fmt, up_count, short_fmt, index_cell, classes
from storkive.__version__ import __url__ as storkive_url
from storkive.__version__ import __version__ as storkive_version


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'storkive_name': settings.STORKIVE_NAME,
        'storkive_url': storkive_url,
        'storkive_version': storkive_version,
        'url': reverse,
    })
    env.filters.update({
        'classes': classes,
        'index_cell': index_cell,
        'intcomma': intcomma,
        'long_fmt': long_fmt,
        'short_fmt': short_fmt,
        'story_count': story_count,
        'up_count': up_count,
    })
    return env
