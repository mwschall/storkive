from django import template
from django.template.defaultfilters import pluralize
from django.utils.formats import date_format as djd_fmt

register = template.Library()


@register.filter
def classes(value):
    return ' '.join([str(v) for v in filter(None, list(value))])


# noinspection PyShadowingBuiltins
@register.filter
def long_fmt(value, format="d F Y"):
    return djd_fmt(value, format=format) if value else ''


# noinspection PyShadowingBuiltins
@register.filter
def short_fmt(value, format="d M Y"):
    return djd_fmt(value, format=format) if value else ''


@register.filter
def index_cell(inst, col):
    if col == 'wc':
        return '%d words' % inst.length if inst.length else '(unknown)'
    elif col == 'cdate':
        return inst.date_published.strftime('%d %b %Y') if inst.date_published else ''
    elif col == 'mdate':
        return inst.date_updated.strftime('%d %b %Y') if inst.date_updated else ''
    else:
        return '—'


@register.filter
def story_count(num):
    return repr(num) + (' story' if num == 1 else ' stories')


@register.filter
def up_count(story):
    count = story.up_count if hasattr(story, 'up_count') else story['up_count']
    if count:
        return '{:d} new chapter{}'.format(count, pluralize(count))
    else:
        return 'revised'

