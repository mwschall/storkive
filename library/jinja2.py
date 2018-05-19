from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment

from library.templatetags.library_extras import story_count, long_fmt, up_count, short_fmt, index_cell


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    env.filters.update({
        'index_cell': index_cell,
        'long_fmt': long_fmt,
        'short_fmt': short_fmt,
        'story_count': story_count,
        'up_count': up_count,
    })
    return env
