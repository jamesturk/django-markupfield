r"""
>>> from django.core import serializers
>>> from markupfield.fields import MarkupField, Markup
>>> from markupfield.widgets import MarkupTextarea, AdminMarkupTextareaWidget
>>> from markupfield.tests.models import Post, Article

# Create a few example posts
>>> mp = Post(title='example markdown post', body='**markdown**', body_markup_type='markdown')
>>> mp.save()
>>> rp = Post(title='example restructuredtext post', body='*ReST*', body_markup_type='ReST')
>>> rp.save()

## Basics ##

# Make sure verbose_name works
>>> mp._meta.get_field('body').verbose_name
'body of post'

# The body attribute is an instance of Markup
>>> mp.body.raw, mp.body.rendered, mp.body.markup_type
('**markdown**', u'<p><strong>markdown</strong></p>', 'markdown')

# Calling unicode on the Markup object gives the rendered string
>>> unicode(rp.body.rendered)
u'<p><em>ReST</em></p>\n'

# The data loads back from the database correctly and 'post' has the right type.
>>> p1 = Post.objects.get(pk=mp.pk)
>>> isinstance(p1.body, Markup)
True
>>> unicode(p1.body)
u'<p><strong>markdown</strong></p>'

## Assignment ##  

# assignment directly to body
>>> rp.body = '**ReST**'
>>> rp.save()
>>> unicode(rp.body)
u'<p><strong>ReST</strong></p>\n'

# assignment to body.raw
>>> rp.body = '*ReST*'
>>> rp.save()
>>> unicode(rp.body)
u'<p><em>ReST</em></p>\n'

# assignment to rendered
>>> rp.body.rendered = 'this should fail'
Traceback (most recent call last):
    ...
AttributeError: can't set attribute

# assignment to body.type
>>> rp.body.markup_type = 'markdown'
>>> rp.save()
>>> rp.body.markup_type, unicode(rp.body)
('markdown', u'<p><em>ReST</em></p>')

## Serialization ##

# serialize to json
>>> stream = serializers.serialize('json', Post.objects.all())
>>> stream
'[{"pk": 1, "model": "tests.post", "fields": {"body": "**markdown**", "_body_rendered": "<p><strong>markdown</strong></p>", "body_markup_type": "markdown", "title": "example markdown post"}}, {"pk": 2, "model": "tests.post", "fields": {"body": "*ReST*", "_body_rendered": "<p><em>ReST</em></p>", "body_markup_type": "markdown", "title": "example restructuredtext post"}}]'

# deserialization
>>> obj = list(serializers.deserialize("json", stream))[0]
>>> obj.object == mp
True

## forms and formfields

# ensure that MarkupTextarea widget is used
>>> isinstance(MarkupField().formfield().widget, MarkupTextarea)
True

# ensure that MarkupTextarea shows the correct text
>>> from django.forms.models import modelform_factory
>>> ArticleForm = modelform_factory(Article)
>>> af = ArticleForm()

# ensure that a field with markup_type set does not have a field (non-editable)
>>> af.fields.keys()
['normal_field', 'default_field', 'normal_field_markup_type', 'markdown_field', 'default_field_markup_type']

# make sure that a markup_type field shows the correct choices
>>> af.fields['normal_field_markup_type'].choices
[('markdown', 'markdown'), ('ReST', 'ReST')]

# test default_markup_type
>>> af.fields['normal_field_markup_type'].initial is None
True
>>> af.fields['default_field_markup_type'].initial
u'markdown'

# test correct fields are used in ModelAdmin
#   borrows from regressiontests/admin_widgets/tests.py
>>> from django.contrib import admin
>>> ma = admin.ModelAdmin(Post, admin.site)
>>> isinstance(ma.formfield_for_dbfield(Post._meta.get_field('body')).widget, AdminMarkupTextareaWidget)
True

"""
