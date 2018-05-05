import base64
import hashlib
import re

from num2words import num2words


# https://stackoverflow.com/a/7001371
def char_range(c1, c2):
    for c in range(ord(c1), ord(c2) + 1):
        yield chr(c)


def b64md5sum(file):
    """Calculate the md5 checksum of a file-like object without reading its
    whole content in memory. Return the value in base64 as required by the
    Content-MD5 header field. Modified from `scrapy.utils.misc.md5sum`.

    >>> from io import BytesIO
    >>> b64md5sum(BytesIO(b'file content to hash'))
    'eEQGr5HdWlT7uchMIjZZWg=='
    """
    m = hashlib.md5()
    while True:
        d = file.read(8096)
        if not d:
            break
        m.update(d)
    return base64.b64encode(m.digest()).decode('utf-8')


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


STORIES_DIR = 'stories'


def inst_path(slug, ordinal, added):
    sort_dir = slug[0].upper()
    sort_dir = sort_dir if re.match(r'[A-Z]', sort_dir) else '_'
    file_name = '{}.{:03d}.{:%Y-%m-%d}.{}'.format(
        slug, ordinal, added, 'html')
    # TODO: make this not break on Windows
    #       form really depends on the django storage in use, or is that handled?
    return '/'.join((STORIES_DIR, sort_dir, slug, file_name))
