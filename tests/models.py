from django.db import models

from markupfield.fields import MarkupField

class Post(models.Model):
    title = models.CharField(max_length=50)
    body = MarkupField('body of post')

    def __unicode__(self):
        return self.title

