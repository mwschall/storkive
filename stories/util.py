import re

from num2words import num2words


# https://stackoverflow.com/a/7001371
def char_range(c1, c2):
    for c in range(ord(c1), ord(c2) + 1):
        yield chr(c)


def get_author_slug(name):
    name = re.sub(r'[,.?!&#‘"“”(){}[\]]', '', name)
    name = re.sub(r'[\'’]', '-', name)
    name = re.sub(r'\*', '_', name)
    name = re.sub(r'[^A-Za-z0-9-_]', '-', name)
    return name


def get_sort_name(name):
    name = name.strip().lstrip('.').lower()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[\'‘’"“”(){}[\]]', '', name)
    name = re.sub(r'^(?:the |a |an )', '', name)
    name = re.sub(r'^(\d+)(?:st|nd|rd|th)\b',
                  lambda m: num2words(int(m.group(1)), to='ordinal'),
                  name)
    name = re.sub(r'^\d{4}', lambda m: num2words(int(m.group()), to='year'), name)
    name = re.sub(r'^\d+', lambda m: num2words(int(m.group())), name)
    return name


def inst_path(slug, ordinal, added):
    sort_dir = slug[0].upper()
    sort_dir = sort_dir if re.match(r'[A-Z]', sort_dir) else '_'
    file_name = '{}.{:03d}.{:%Y-%m-%d}.{}'.format(
        slug, ordinal, added, 'html')
    # NOTE: Scrapy file stores expect a standard path
    return '/'.join((sort_dir, slug, file_name))
