import django
from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.html import escape

from markupfield import markup

_rendered_field_name = lambda name: '_%s_rendered' % name
_markup_type_field_name = lambda name: '%s_markup_type' % name

# for fields that don't set markup_types: detected types or from settings
_MARKUP_TYPES = getattr(settings, 'MARKUP_FIELD_TYPES', markup.DEFAULT_MARKUP_TYPES)


class Markup(object):

    def __init__(self, instance, field_name, rendered_field_name,
                 markup_type_field_name):
        # instead of storing actual values store a reference to the instance
        # along with field names, this makes assignment possible
        self.instance = instance
        self.field_name = field_name
        self.rendered_field_name = rendered_field_name
        self.markup_type_field_name = markup_type_field_name

    # raw is read/write
    def _get_raw(self):
        return self.instance.__dict__[self.field_name]

    def _set_raw(self, val):
        setattr(self.instance, self.field_name, val)

    raw = property(_get_raw, _set_raw)

    # markup_type is read/write
    def _get_markup_type(self):
        return self.instance.__dict__[self.markup_type_field_name]

    def _set_markup_type(self, val):
        return setattr(self.instance, self.markup_type_field_name, val)

    markup_type = property(_get_markup_type, _set_markup_type)

    # rendered is a read only property
    def _get_rendered(self):
        return getattr(self.instance, self.rendered_field_name)
    rendered = property(_get_rendered)

    # allows display via templates to work without safe filter
    def __unicode__(self):
        return mark_safe(self.rendered)


class MarkupDescriptor(object):

    def __init__(self, field):
        self.field = field
        self.rendered_field_name = _rendered_field_name(self.field.name)
        self.markup_type_field_name = _markup_type_field_name(self.field.name)

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError('Can only be accessed via an instance.')
        markup = instance.__dict__[self.field.name]
        if markup is None:
            return None
        return Markup(instance, self.field.name, self.rendered_field_name,
                      self.markup_type_field_name)

    def __set__(self, obj, value):
        if isinstance(value, Markup):
            obj.__dict__[self.field.name] = value.raw
            setattr(obj, self.rendered_field_name, value.rendered)
            setattr(obj, self.markup_type_field_name, value.markup_type)
        else:
            obj.__dict__[self.field.name] = value


class MarkupField(models.TextField):

    def __init__(self, verbose_name=None, name=None, markup_type=None,
                 default_markup_type=None, markup_choices=_MARKUP_TYPES,
                 escape_html=False, **kwargs):

        if markup_type and default_markup_type:
            raise ValueError('Cannot specify both markup_type and default_markup_type')

        self.default_markup_type = markup_type or default_markup_type
        self.markup_type_editable = markup_type is None
        self.escape_html = escape_html

        # pre 1.0 markup_choices might have been a dict
        if isinstance(markup_choices, dict):
            raise DeprecationWarning('passing a dictionary as markup_choices is deprecated')
            self.markup_choices_dict = markup_choices
            self.markup_choices_list = markup_choices.keys()
        else:
            self.markup_choices_list = [mc[0] for mc in markup_choices]
            self.markup_choices_dict = dict(markup_choices)

        if (self.default_markup_type and
            self.default_markup_type not in self.markup_choices_list):
            raise ValueError("Invalid default_markup_type for field '%s', allowed values: %s" %
                             (name, ', '.join(self.markup_choices_list)))

        # for South FakeORM compatibility: the frozen version of a
        # MarkupField can't try to add a _rendered field, because the
        # _rendered field itself is frozen as well. See introspection
        # rules below.
        self.rendered_field = not kwargs.pop('rendered_field', False)

        super(MarkupField, self).__init__(verbose_name, name, **kwargs)

    def contribute_to_class(self, cls, name):
        if not cls._meta.abstract:
            choices = zip(self.markup_choices_list, self.markup_choices_list)
            markup_type_field = models.CharField(max_length=30,
                choices=choices, default=self.default_markup_type,
                editable=self.markup_type_editable, blank=self.blank)
            rendered_field = models.TextField(editable=False)
            markup_type_field.creation_counter = self.creation_counter+1
            rendered_field.creation_counter = self.creation_counter+2
            cls.add_to_class(_markup_type_field_name(name), markup_type_field)
            cls.add_to_class(_rendered_field_name(name), rendered_field)
        super(MarkupField, self).contribute_to_class(cls, name)

        setattr(cls, self.name, MarkupDescriptor(self))

    def pre_save(self, model_instance, add):
        value = super(MarkupField, self).pre_save(model_instance, add)
        if value.markup_type not in self.markup_choices_list:
            raise ValueError('Invalid markup type (%s), allowed values: %s' %
                             (value.markup_type,
                              ', '.join(self.markup_choices_list)))
        if self.escape_html:
            raw = escape(value.raw)
        else:
            raw = value.raw
        rendered = self.markup_choices_dict[value.markup_type](raw)
        setattr(model_instance, _rendered_field_name(self.attname), rendered)
        return value.raw

    def get_prep_value(self, value):
        if isinstance(value, Markup):
            return value.raw
        else:
            return value

    # copy get_prep_value to get_db_prep_value if pre-1.2
    if django.VERSION < (1,2):
        get_db_prep_value = get_prep_value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return value.raw

    def value_from_object(self, obj):
        return super(MarkupField, self).value_from_object(obj).raw


# allow South to handle MarkupField smoothly
try:
    from south.modelsinspector import add_introspection_rules
    # For a normal MarkupField, the add_rendered_field attribute is
    # always True, which means no_rendered_field arg will always be
    # True in a frozen MarkupField, which is what we want.
    add_introspection_rules(rules=[
        ( (MarkupField,), [], { 'rendered_field': ['rendered_field', {}], })
    ], patterns=['markupfield\.fields\.MarkupField'])
except ImportError:
    pass
