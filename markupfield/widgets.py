from django import forms
from django.forms.util import flatatt
from django.utils.safestring import mark_safe


class MarkupTextarea(forms.widgets.Textarea):

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        else:
            value = value.raw
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(u'<textarea%s>%s</textarea>' %
                         (flatatt(final_attrs), value))


class AdminMarkupTextareaWidget(MarkupTextarea):

    def __init__(self, attrs=None):
        final_attrs = {'class': 'vLargeTextField'}
        if attrs is not None:
            final_attrs.update(attrs)
        super(AdminMarkupTextareaWidget, self).__init__(attrs=final_attrs)
