from django.db import models


class CssField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 25
        super().__init__(*args, **kwargs)
