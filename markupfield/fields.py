import django
from django.conf import settings
from django.core import checks
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.encoding import smart_text

from markupfield import widgets
from markupfield import markup

# for fields that don't set markup_types: detected types or from settings
_MARKUP_TYPES = getattr(settings, 'MARKUP_FIELD_TYPES',
                        markup.DEFAULT_MARKUP_TYPES)


class Markup(object):
    def __init__(self, instance, field):
        self.instance = instance
        self.field = field

        # Initialize the convenience attributes.
        self._update_rendered()

    def _update_rendered(self):
        # Update the rendered text.
        if self.field.rendered_field:
            setattr(
                self.instance,
                self.field.rendered_field,
                self.field.markup_choices_dict[self.markup_type](
                    escape(self.raw) if self.field.escape_html else self.raw
                )
            )
        else:
            self._rendered = (
                self.field.markup_choices_dict[self.markup_type](
                    escape(self.raw) if self.field.escape_html else self.raw
                )
            )

    def _get_raw(self):
        return self.instance.__dict__[self.field.name]

    def _set_raw(self, val):
        if val != self.raw:
            self.instance.__dict__[self.field.name] = val
            self._update_rendered()

    raw = property(_get_raw, _set_raw)

    def _get_markup_type(self):
        if self.field.markup_type_field:
            return getattr(self.instance, self.field.markup_type_field)
        if self.field.markup_type:
            return self.field.markup_type
        if self.field.default_markup_type:
            return self.field.default_markup_type
        return None

    def _set_markup_type(self, val):
        if val != self.markup_type:
            if self.field.markup_type_field:
                if val not in self.field.markup_choices_list:
                    raise ValueError(
                        "Invalid default_markup_type for field '%s', "
                        "allowed values: %s" % (
                            self.field.name,
                            ', '.join(self.field.markup_choices_list)
                        )
                    )
                setattr(self.instance, self.field.markup_type_field, val)
            else:
                self.field.markup_type = val

            self._update_rendered()

    markup_type = property(_get_markup_type, _set_markup_type)

    def _get_rendered(self):
        if self.field.rendered_field:
            return getattr(self.instance, self.field.rendered_field)
        return self._rendered
    rendered = property(_get_rendered)

    # allows display via templates to work without safe filter
    def __unicode__(self):
        return mark_safe(smart_text(self.rendered))

    __str__ = __unicode__


class MarkupDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))

        markup = instance.__dict__[self.field.name]
        if markup is None:
            return None

        return self.field.attr_class(instance, self.field)

    def __set__(self, instance, value):
        if isinstance(value, self.field.attr_class):
            instance.__dict__[self.field.name] = value.raw

            if self.field.rendered_field:
                setattr(instance, self.field.rendered_field,
                        value.rendered)
            if self.field.markup_type_field:
                setattr(instance, self.field.markup_type_field,
                        value.markup_type)
        else:
            instance.__dict__[self.field.name] = value


class MarkupField(models.TextField):
    descriptor_class = MarkupDescriptor
    attr_class = Markup

    def __init__(self, markup_type=None, rendered_field=None,
                 markup_type_field=None, default_markup_type=None,
                 escape_html=False, markup_choices=_MARKUP_TYPES,
                 *args, **kwargs):
        self.markup_type = markup_type
        self.rendered_field = rendered_field
        self.markup_type_field = markup_type_field
        self.default_markup_type = default_markup_type
        self.escape_html = escape_html
        self.markup_choices = markup_choices

        self.markup_choices_list = [mc[0] for mc in markup_choices]
        self.markup_choices_dict = dict(markup_choices)

        super(MarkupField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, virtual_only=False):
        if django.VERSION < (1, 7):
            super(MarkupField, self).contribute_to_class(cls, name)
        else:
            super(MarkupField, self).contribute_to_class(
                cls, name, virtual_only=virtual_only
            )
        setattr(cls, self.name, self.descriptor_class(self))

    def pre_save(self, model_instance, add):
        value = super(MarkupField, self).pre_save(model_instance, add)

        if value.markup_type not in self.markup_choices_list:
            raise ValueError(
                'Invalid markup type (%s), allowed values: %s' % (
                    value.markup_type,
                    ', '.join(self.markup_choices_list)
                )
            )

        if self.field.rendered_field:
            value._update_rendered()

        return value.raw

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        if hasattr(value, 'raw'):
            return value.raw
        return value

    def formfield(self, **kwargs):
        defaults = {'widget': widgets.MarkupTextarea}
        defaults.update(kwargs)
        return super(MarkupField, self).formfield(**defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(MarkupField, self).deconstruct()

        if self.markup_type:
            kwargs['markup_type'] = self.markup_type
        if self.rendered_field:
            kwargs['rendered_field'] = self.rendered_field
        if self.markup_type_field:
            kwargs['markup_type_field'] = self.markup_type_field
        if self.default_markup_type:
            kwargs['default_markup_type'] = self.default_markup_type
        if self.escape_html:
            kwargs['escape_html'] = self.escape_html
        kwargs['markup_choices'] = self.markup_choices

        return name, path, args, kwargs

    def _check_markup_type_vs_default_markup_type(self):
        if self.markup_type and self.default_markup_type:
            return [
                checks.Error(
                    ("Do not supply both 'markup_type' and "
                     "'default_markup_type'."),
                    obj=self,
                )
            ]
        return []

    def _check_default_markup_type_vs_markup_type_field(self):
        if self.default_markup_type and self.markup_type_field:
            return [
                checks.Warning(
                    ('The default markup type should be supplied to the '
                     'markup type field, not to the MarkupField instance.'),
                    obj=self,
                    hint=(
                        "Move your 'default_markup_type' parameter to the "
                        "field you specified as your 'markup_type_field'."
                    )
                )
            ]
        return []

    def check(self, **kwargs):
        errors = super(MarkupField, self).check(**kwargs)
        errors.extend(self._check_markup_type_vs_default_markup_type())
        errors.extend(self._check_default_markup_type_vs_markup_type_field())
        return errors


# register MarkupField to use the custom widget in the Admin
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
FORMFIELD_FOR_DBFIELD_DEFAULTS[MarkupField] = {
    'widget': widgets.AdminMarkupTextareaWidget
}
