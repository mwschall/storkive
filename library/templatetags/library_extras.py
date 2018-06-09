from django import template
from django.template.defaultfilters import pluralize
from django.utils.formats import date_format as djd_fmt
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def classes(value):
    return ' '.join(filter(None, value))


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


@register.filter(is_safe=True)
def up_count(story, up_date):
    if story.published_on == up_date:
        result = '<strong>(new)</strong>'
    else:
        cnt = story.up_cnt
        result = '({:d} new chapter{})'.format(cnt, pluralize(cnt))
    return mark_safe(result)
