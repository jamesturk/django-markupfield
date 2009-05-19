from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.core.exceptions import ImproperlyConfigured
import widgets

_rendered_field_name = lambda name: '%s_rendered' % name

def _load_renderer(path):
    """
    Attempt to load a callable to use as a renderer, eg. markdown.markdown
    """
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = __import__(module, {}, {}, [attr])
    except ImportError, e:
        raise ImproperlyConfigured('Error importing markup processor module %s: "%s"' % (module, e))
    try:
        return getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" callable request processor' % (module, attr))

class Markup(object):
    def __init__(self, instance, field_name, rendered_field_name):
        # instead of storing actual values store a reference to the instance
        # along with field names, this makes possible assignment to raw and
        # allows save_markup to alter the rendered column on the instance itself
        print 'M.__init__'
        self.instance = instance
        self.field_name = field_name
        self.rendered_field_name = rendered_field_name

    # raw allows access to the underlying field
    def _get_raw(self):
        return self.instance.__dict__[self.field_name]
    def _set_raw(self, val):
        setattr(self.instance, self.field_name, val)
    raw = property(_get_raw, _set_raw)

    # rendered is a read only property
    def _get_rendered(self):
        return getattr(self.instance, self.rendered_field_name)
    rendered = property(_get_rendered)

    # save_markup('markdown.markdown') or save_markup(markdown.markdown)
    def save_markup(self, formatter, **kwargs):
        print 'save_markup'
        if not callable(formatter):
            formatter = _load_renderer(formatter)
        setattr(self.instance, self.rendered_field_name, formatter(self.raw))

    # allows display via templates to work without safe filter
    def __unicode__(self):
        return mark_safe(self.rendered)

class MarkupDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.rendered_field_name = _rendered_field_name(self.field.name)

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError('Can only be accessed via an instance.')
        markup = instance.__dict__[self.field.name]
        if markup is None:
            return None
        return Markup(instance, self.field.name, self.rendered_field_name)

    def __set__(self, obj, value):
        if isinstance(value, Markup):
            obj.__dict__[self.field.name] = value.raw
            setattr(obj, self.rendered_field_name, value.rendered)
        else:
            obj.__dict__[self.field.name] = value

class MarkupField(models.TextField):

    def __init__(self, verbose_name=None, name=None, formatter=None,
                 formatter_kwargs=None, **kwargs):
        format = formatter or settings.DEFAULT_MARKUP_FILTER['formatter']
        self.formatter_kwargs = formatter_kwargs or settings.DEFAULT_MARKUP_FILTER['kwargs']
        if callable(format):
            self.formatter = format
        else:
            self.formatter = _load_renderer(format)

        super(MarkupField, self).__init__(verbose_name, name, **kwargs)

    def contribute_to_class(self, cls, name):
        rendered_field = models.TextField(editable=False)
        rendered_field.creation_counter = self.creation_counter+1
        cls.add_to_class(_rendered_field_name(name), rendered_field)
        super(MarkupField, self).contribute_to_class(cls, name)

        setattr(cls, self.name, MarkupDescriptor(self))

    def pre_save(self, model_instance, add):
        value = super(MarkupField, self).pre_save(model_instance, add).raw
        print 'pre_save'
        rendered = self.formatter(value)
        setattr(model_instance, _rendered_field_name(self.attname), rendered)
        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return value.raw

    def formfield(self, **kwargs):
        defaults = {'widget': widgets.MarkupTextarea}
        defaults.update(kwargs)
        return super(MarkupField, self).formfield(**defaults)

# register MarkupField to use the custom widget in the Admin
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
FORMFIELD_FOR_DBFIELD_DEFAULTS[MarkupField] = {'widget': widgets.AdminMarkupTextareaWidget}
