from collections import Iterable

from library.util import get_author_slug

DEFAULT_AUTHOR_SEP = '|'
CODE_SEP = ','


# noinspection PyAttributeOutsideInit
class AuthorsMixin(object):
    _author_sort = True

    @property
    def author_dicts(self):
        dicts = self._author_dicts
        return dicts

    @author_dicts.setter
    def author_dicts(self, value):
        values = value.split(DEFAULT_AUTHOR_SEP)
        if self._author_sort:
            values = sorted(set(values), key=lambda n: n.casefold())
        self._author_dicts = [
            {'name': name, 'slug': get_author_slug(name)}
            for name in values
        ]


# noinspection PyAttributeOutsideInit
class CodesMixin(object):

    @property
    def code_abbrs(self):
        return self._code_abbrs

    @code_abbrs.setter
    def code_abbrs(self, value):
        if isinstance(value, str):
            self._code_abbrs = value.split(CODE_SEP)
        elif isinstance(value, Iterable):
            self._code_abbrs = value
        else:
            self._code_abbrs = []
