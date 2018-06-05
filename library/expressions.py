from django.db import models
from django.db.models import Subquery, CharField, Func

# NOTE: not EVERYTHING needs to be an Aggregate, yo
#       https://docs.djangoproject.com/en/2.0/ref/models/expressions/#func-expressions


# https://stackoverflow.com/a/31337612
# noinspection PyAbstractClass
class Concat(Func):
    function = 'GROUP_CONCAT'
    template = "%(function)s(%(distinct)s%(expressions)s, '%(separator)s')"

    def __init__(self, expression, separator=',', distinct=False, **extra):
        super(Concat, self).__init__(
            expression,
            separator=separator,
            distinct='DISTINCT ' if distinct else '',
            output_field=CharField(),
            **extra)

    def as_postgresql(self, compiler, connection):
        return self.as_sql(compiler, connection, function='string_agg')


# noinspection PyAbstractClass
class SQCount(Subquery):
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = models.IntegerField()

    def get_source_expressions(self):
        return []


# noinspection PyAbstractClass
class ChillSubquery(Subquery):
    # chill the F out and don't explode the GROUP BY clause
    def get_source_expressions(self):
        return []
