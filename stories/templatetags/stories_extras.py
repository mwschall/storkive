from django import template
from django.template.defaultfilters import pluralize
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def index_cell(inst, col):
    if col == 'wc':
        return '%d words' % inst.length if inst.length else '(unknown)'
    elif col == 'cdate':
        return inst.date_added.strftime('%d %b %Y')
    elif col == 'mdate':
        return inst.date_updated.strftime('%d %b %Y') if inst.date_updated else ''
    else:
        result = '—'

    return result


@register.filter
def story_count(num):
    return repr(num) + (' story' if num == 1 else ' stories')


@register.filter(is_safe=True)
def up_count(story, up_date):
    if story.added == up_date:
        result = '<strong> (new)</strong>'
    else:
        cnt = story.up_cnt
        result = ' ({:d} new chapter{})'.format(cnt, pluralize(cnt))
    return mark_safe(result)
