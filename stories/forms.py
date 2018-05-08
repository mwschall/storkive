from django import forms

from stories.util import clean_paragraph, fix_line_endings


class NormalizingCharField(forms.CharField):
    def __init__(self, *, multiline=False, **kwargs):
        self.multiline = multiline
        kwargs.update(strip=True)
        super().__init__(**kwargs)

    def to_python(self, value):
        value = super(NormalizingCharField, self).to_python(value)
        return clean_paragraph(value, multiline=self.multiline)


class TextField(forms.CharField):
    def __init__(self, **kwargs):
        kwargs.update(strip=False)
        super().__init__(**kwargs)

    def to_python(self, value):
        value = super(TextField, self).to_python(value)
        return fix_line_endings(value)
