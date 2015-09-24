from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from markupfield.fields import MarkupField


@python_2_unicode_compatible
class Post(models.Model):
    title = models.CharField(max_length=50)
    body = MarkupField('body of post')
    comment = MarkupField(escape_html=True, default_markup_type='markdown')

    def __str__(self):
        return self.title


class Article(models.Model):
    normal_field = MarkupField()
    markup_choices_field = MarkupField(markup_choices=(
        ('pandamarkup', lambda x: 'panda'),
        ('nomarkup', lambda x: x),
        ('fancy', lambda x: x[::-1], 'Some fancy Markup'),  # String reverse
    ))
    default_field = MarkupField(default_markup_type='markdown')
    markdown_field = MarkupField(markup_type='markdown')


class Abstract(models.Model):
    content = MarkupField()

    class Meta:
        abstract = True


class Concrete(Abstract):
    pass


class NullTestModel(models.Model):
    text = MarkupField(null=True, blank=True, default=None, default_markup_type="markdown")


class DefaultTestModel(models.Model):
    text = MarkupField(null=True, default="**nice**", default_markup_type="markdown")
