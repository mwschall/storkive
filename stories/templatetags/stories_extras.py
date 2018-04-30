from django import template

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
def codes_cell(tags):
    return ' '.join([tag.abbr for tag in tags.all()])


# @register.filter(needs_autoescape=True)
# def index_cell(inst, col, autoescape=True):
#     if autoescape:
#         esc = conditional_escape
#     else:
#         esc = lambda x: x
#
#     if col == 'chapter':
#         url = reverse()
#         result = '<a href="%s">%s</a>' % (url(inst['']), esc(inst['title']))
#     else:
#         result = '—'
#
#     return mark_safe(result)
