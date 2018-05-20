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


# NOTE: these aren't exact, but should be safe enough
re_css_colors = [
    re.compile(r'^#[0-9A-F]{3}|#[0-9A-F]{6}$', re.I),                 # hex
    re.compile(r'^rgba?\(\d+,\d+,\d+(?:,(?:0?\.)?\d+)?\)$', re.I),    # rgb(a)
    re.compile(r'^hsla?\(\d+,\d+%,\d+%(?:,(?:0?\.)?\d+)?\)$', re.I),  # hsl(a)
    re.compile(r'^[a-z]{0,25}$', re.I),                               # names
]


def is_css_color(color):
    color = re.sub(r'\s+', '', color)
    for pat in re_css_colors:
        if re.match(pat, color):
            return True


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


def inst_path(slug, ordinal, added_at):
    sort_dir = slug[0].upper()
    sort_dir = sort_dir if re.match(r'[A-Z]', sort_dir) else '_'
    file_name = '{}.{:03d}.{:%Y-%m-%d}.{}'.format(
        slug, ordinal, added_at, 'html')
    # TODO: make this not break on Windows
    #       form really depends on the django storage in use, or is that handled?
    return '/'.join((STORIES_DIR, sort_dir, slug, file_name))


re_space_any = re.compile(r'\s+')
re_squote = re.compile(r'(?:(^|\s)|(.))(["\'])(.|$)', re.M)


def _quote_fancier(m):
    # TODO: test this, please
    # NOTE: account for: “Down the center path—“
    style = ('‘', '’') if m.group(3) is '\'' else ('“', '”')
    new_quote = style[0] if m.group(1) is not None else style[1]
    repl = (m.group(1), m.group(2), new_quote, m.group(4))
    return ''.join([s for s in repl if s])


def fancy_quote(text):
    return re.sub(re_squote, _quote_fancier, text)


def plain_quote(text):
    return re.sub(r'([‘’])|([“”])', lambda m: "'" if m.group(1) else '"', text)


def fix_line_endings(text):
    return re.sub(r'\r\n|\n\r|\r', '\n', text)


def clean_whitespace(text, multiline=False):
    text = text.strip()
    if multiline:
        text = fix_line_endings(text)
        text = re.sub(r'[\f\v]', '\n', text)
        text = re.sub(r' +', ' ', text)
        # TODO: what about tabs?
    else:
        text = re.sub(r'\s+', ' ', text)
    return text


def clean_paragraph(text, multiline=False):
    text = clean_whitespace(text, multiline)
    text = fancy_quote(text)
    return text
