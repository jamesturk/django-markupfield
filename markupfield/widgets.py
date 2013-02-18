from django import forms
from django.contrib.admin.widgets import AdminTextareaWidget
from django.utils import six


class MarkupTextarea(forms.widgets.Textarea):

    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, six.text_type):
            value = value.raw
        return super(MarkupTextarea, self).render(name, value, attrs)


class AdminMarkupTextareaWidget(MarkupTextarea, AdminTextareaWidget):
    pass
