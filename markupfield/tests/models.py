from django.db import models

from markupfield.fields import MarkupField

class Post(models.Model):
    title = models.CharField(max_length=50)
    body = MarkupField('body of post')

    def __unicode__(self):
        return self.title

class Article(models.Model):
    normal_field = MarkupField()
    default_field = MarkupField(default_markup_type='markdown')
    markdown_field = MarkupField(markup_type='markdown')

class Abstract(models.Model):
    content = MarkupField()

    class Meta:
        abstract = True

class Concrete(Abstract):
    pass
