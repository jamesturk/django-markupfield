import django
from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.encoding import smart_text

from markupfield import widgets
from markupfield import markup

try:
    from django.core import checks
except ImportError:
    # I guess this isn't Django 1.7+.
    pass

# For fields that don't set markup_types: detected types or from settings.
_MARKUP_TYPES = getattr(settings, 'MARKUP_FIELD_TYPES',
                        markup.DEFAULT_MARKUP_TYPES)


class MarkupFieldError(Exception):
    pass


class Markup(object):
    def __init__(self, instance, field):
        self.instance = instance
        self.field = field

        # Force an initialization of the rendered field. Due to the possibility
        # of update() and similar Django functions, we have to be suspicious of
        # any existing database value.
        self._update_rendered()

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
        raise MarkupFieldError('No markup type type or markup type field '
                               'given for field {}.'.format(self.field.name))

    def _set_markup_type(self, val):
        if val != self.markup_type:
            if self.field.markup_type_field:
                if val not in self.field.markup_choices_list:
                    raise MarkupFieldError(
                        "Invalid markup type for field '{field_name}', "
                        'allowed values: {allowed}'.format(
                            field_name=self.field.name,
                            allowed=', '.join(self.field.markup_choices_list)
                        )
                    )
                setattr(self.instance, self.field.markup_type_field, val)
            else:
                self.field.markup_type = val

            self._update_rendered()

    markup_type = property(_get_markup_type, _set_markup_type)

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
            raise AttributeError((
                "The '{}' attribute can only be accessed from {} instances."
            ).format(self.field.name, owner.__name__))

        if instance.__dict__[self.field.name] is None:
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

        # To bootstrap the population of the rendered field, call the field.
        getattr(instance, self.field.name)


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

        if django.VERSION < (1, 7):
            # Check for hard errors in Django 1.6 and under.
            errors = map(lambda x: '{}: {}'.format(self.name, x),
                         self.checks())
            if errors:
                raise MarkupFieldError('\n\n'.join(errors))

        super(MarkupField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, virtual_only=False):
        try:
            # virtual_only isn't documented, and it's used in some places but
            # not others. We'll try to use it.
            super(MarkupField, self).contribute_to_class(
                cls, name, virtual_only=virtual_only
            )
        except TypeError:
            super(MarkupField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def pre_save(self, model_instance, add):
        value = super(MarkupField, self).pre_save(model_instance, add)

        if value.markup_type not in self.markup_choices_list:
            raise MarkupFieldError((
                "Invalid markup type '{}', allowed values: {}"
            ).format(value.markup_type, ', '.join(self.markup_choices_list)))

        return value.raw

    def get_prep_value(self, value):
        if isinstance(value, self.attr_class):
            return value.raw
        else:
            return value

    if django.VERSION < (1, 2):
        get_db_prep_value = get_prep_value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        if isinstance(value, self.attr_class):
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
            msg = "Do not supply both 'markup_type' and 'default_markup_type'."

            if django.VERSION >= (1, 7):
                return [checks.Error(msg, obj=self)]
            return [msg]
        return []

    def _check_default_markup_type_vs_markup_type_field(self):
        if django.VERSION < (1, 7):
            # We are only concerned with hard errors in older versions.
            return []

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

    def _check_markup_type_field_or_markup_type(self):
        if not any((self.markup_type_field, self.markup_type)):
            msg = (
                "You must provide either 'markup_type_field' or 'markup_type'."
            )

            if django.VERSION >= (1, 7):
                return [checks.Error(msg, obj=self)]
            return [msg]
        return []

    def _check_default_markup_type_and_markup_type_field(self):
        if self.default_markup_type and not self.markup_type_field:
            msg = (
                "'default_markup_type' is provided without "
                "'markup_type_field'."
            )

            if django.VERSION >= (1, 7):
                return [
                    checks.Error(
                        msg,
                        obj=self,
                        hint=(
                            'Providing a default markup type implies that the '
                            'user will be able to choose and store the markup '
                            "type, which can't be done without a dedicated "
                            'markup field. Please provide one.'
                        )
                    )
                ]
            return [msg]
        return []

    def _check_default_markup_type_is_valid(self):
        if (self.default_markup_type
                and self.default_markup_type not in self.markup_choices_list):
            msg = (
                "Invalid 'default_markup_type'. Allowed choices: {}"
            ).format(', '.join(self.markup_choices_list))

            if django.VERSION >= (1, 7):
                return [checks.Error(msg, obj=self)]
            return [msg]
        return []

    def check(self, **kwargs):
        if django.VERSION >= (1, 7):
            errors = super(MarkupField, self).check(**kwargs)
        else:
            errors = []

        errors.extend(self._check_markup_type_vs_default_markup_type())
        errors.extend(self._check_default_markup_type_vs_markup_type_field())
        errors.extend(self._check_markup_type_field_or_markup_type())
        errors.extend(self._check_default_markup_type_is_valid())
        errors.extend(self._check_default_markup_type_and_markup_type_field())
        errors.extend(self._check_default_markup_type_is_valid())
        return errors


# register MarkupField to use the custom widget in the Admin
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
FORMFIELD_FOR_DBFIELD_DEFAULTS[MarkupField] = {
    'widget': widgets.AdminMarkupTextareaWidget
}
