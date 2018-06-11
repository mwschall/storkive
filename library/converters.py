from library.fields import ShortUUIDField
from library.util import shortuuid


# noinspection PyMethodMayBeStatic
class FourDigitYearConverter:
    regex = '[0-9]{4}'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return '%04d' % value


# noinspection PyMethodMayBeStatic
class ShortUUIDConverter:
    regex = '[%s]{%s}' % (shortuuid.get_alphabet(), ShortUUIDField.DEFAULT_LEN)

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
