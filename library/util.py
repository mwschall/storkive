import base64
import hashlib
import re

import shortuuid
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


# don't use ambiguous characters, because reasons
shortuuid.set_alphabet('23456789ABCDEFGHJKLMNPQRSTUVWXYZ')


# https://github.com/skorokithakis/shortuuid
def s_uuid(length=22):
    return shortuuid.uuid()[:length]


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
    name = re.sub(r'[,.?!#$‘"“”(){}[\]]', '', name)
    # name = re.sub(r'[*&\'’]', '-', name)
    name = re.sub(r'[^-_A-Za-z0-9]', '-', name)
    name = name.strip('-')
    return name


def get_sort_name(name):
    name = name.strip().lstrip('.').lower()

    # normalize whitespace
    name = re.sub(r'\s+', ' ', name)

    # sort apostrophes within words last, because reasons... or don't
    # name = re.sub(r'(?<=\w)[\'’](?=\w)', '~', name)

    # drop apostrophes and quotes
    name = re.sub(r'[\'‘’"“”]', '', name)

    # get rid of 'cheeky parens'
    # aka when strings of contiguous, non-space characters are partially wrapped
    name = re.sub(r'(?:(?<=^)|(?<=\s))'         # the beginning or a space
                  r'(?P<pre>[^(\s]+)?'          # some non-wrapped characters?
                  r'\((\S+)\)'                  # the wrapped characters
                  r'((?(pre)[^\s)]*|[^\s)]+))'  # require something if no pre-chars
                  r'(?=\s|$)',                  # a space or the end
                  r'\1\2\3', name)

    # drop articles from the beginning
    name = re.sub(r'^(?:the |a (?!(?:to|is) )|an )', '', name)

    # transform numbers to words
    name = re.sub(r'^(\d+)(?:st|nd|rd|th)\b',
                  lambda m: num2words(int(m.group(1)), to='ordinal'),
                  name)
    name = re.sub(r'^\d{4}', lambda m: num2words(int(m.group()), to='year'), name)
    name = re.sub(r'^\d+', lambda m: num2words(int(m.group())), name)

    # kill off any remaining non-letters at the beginning
    name = re.sub(r'^[^a-z]+', '', name)

    return name


STORIES_DIR = 'stories'


def inst_path(slug, ordinal, published_on):
    sort_dir = slug[0].upper()
    sort_dir = sort_dir if re.match(r'[A-Z]', sort_dir) else '_'
    file_name = '{}.{:03d}.{:%Y-%m-%d}.{}'.format(
        slug, ordinal, published_on, 'html')
    # TODO: make this not break on Windows
    #       form really depends on the django storage in use, or is that handled?
    return '/'.join((STORIES_DIR, sort_dir, slug, file_name))


re_space_any = re.compile(r'\s+')
re_squote = re.compile(r'(?:(^|\s)|(.))(["\'])(.|$)', re.M)


def _quote_fancier(m):
    # TODO: test this, please
    # NOTE: account for: “Down the center path—“
    style = ('‘', '’') if m.group(3) == '\'' else ('“', '”')
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
