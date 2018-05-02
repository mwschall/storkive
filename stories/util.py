import os.path
import re

from num2words import num2words


# https://stackoverflow.com/a/7001371
def char_range(c1, c2):
    for c in range(ord(c1), ord(c2) + 1):
        yield chr(c)


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


def get_story_path(slug):
    if not isinstance(slug, str):
        try:
            slug = slug.slug
        except AttributeError:
            slug = slug['slug']
    letter = slug[0].upper()
    letter = letter if re.match(r'[A-Z]', letter) else '_'
    return os.path.join(letter, slug)
