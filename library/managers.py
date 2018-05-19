from django.db import models
from django.db.models.functions import Lower


class OrderedLowerManager(models.Manager):

    def __init__(self, sort_field='name'):
        super(OrderedLowerManager, self).__init__()
        self._sort_field = sort_field

    def get_queryset(self):
        return super().get_queryset().order_by(Lower(self._sort_field))
