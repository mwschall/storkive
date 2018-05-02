from django.db import models
from django.db.models import Subquery


# noinspection PyAbstractClass
class SQCount(Subquery):
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = models.IntegerField()

    def get_source_expressions(self):
        return []
