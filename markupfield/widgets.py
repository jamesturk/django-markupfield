from django import forms
from django.contrib.admin.widgets import AdminTextareaWidget


class MarkupTextarea(forms.widgets.Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        if hasattr(value, "raw"):
            value = value.raw
        return super(MarkupTextarea, self).render(name, value, attrs, renderer=renderer)


class AdminMarkupTextareaWidget(MarkupTextarea, AdminTextareaWidget):
    pass
