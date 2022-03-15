from django.db import models
from django.db.models import Subquery, CharField, Func

# NOTE: not EVERYTHING needs to be an Aggregate, yo
#       https://docs.djangoproject.com/en/2.0/ref/models/expressions/#func-expressions


# https://stackoverflow.com/a/31337612
# noinspection PyAbstractClass
class Concat(Func):
    function = 'GROUP_CONCAT'
    template = "%(function)s(%(distinct)s%(expressions)s%(separator)s)"
    sep_template = ", '%s'"

    def __init__(self, expression, separator=',', distinct=False, **extra):
        # sqlite is limited in this way
        assert separator == ',' or not distinct, \
            'Cannot specify custom separator with distinct clause.'

        super().__init__(
            expression,
            separator=self.sep_template % separator,
            distinct='DISTINCT ' if distinct else '',
            output_field=CharField(),
            **extra)

    def as_sqlite(self, compiler, connection, **extra_context):
        # sqlite expects only one argument when using DISTINCT
        if self.extra['distinct']:
            extra_context['separator'] = ''
        return self.as_sql(compiler, connection, **extra_context)

    def as_postgresql(self, compiler, connection):
        return self.as_sql(compiler, connection, function='string_agg')


# noinspection PyAbstractClass
class SQCount(Subquery):
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = models.IntegerField()


# noinspection PyAbstractClass
class ChillSubquery(Subquery):
    # chill the F out and don't explode the GROUP BY clause
    # TODO: is this still necessary?
    pass
