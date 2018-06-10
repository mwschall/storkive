from django.db import models

from library.util import s_uuid


class CssField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 25
        super().__init__(*args, **kwargs)


class ShortUUIDField(models.CharField):
    DEFAULT_LEN = 8

    def __init__(self, *args, **kwargs):
        kwargs['default'] = ShortUUIDField.gen
        kwargs['max_length'] = ShortUUIDField.DEFAULT_LEN
        super().__init__(*args, **kwargs)

    @staticmethod
    def gen():
        return s_uuid(ShortUUIDField.DEFAULT_LEN)
