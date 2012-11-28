from django.test import TestCase
from django.core import serializers
from markupfield.fields import MarkupField, Markup
from markupfield.widgets import MarkupTextarea, AdminMarkupTextareaWidget
from markupfield.tests.models import Post, Article, Concrete

from django.forms.models import modelform_factory
ArticleForm = modelform_factory(Article)

class MarkupFieldTestCase(TestCase):

    def setUp(self):
        self.xss_str = "<script>alert('xss');</script>"
        self.mp = Post(title='example markdown post', body='**markdown**',
                       body_markup_type='markdown')
        self.mp.save()
        self.rp = Post(title='example restructuredtext post', body='*ReST*',
                       body_markup_type='ReST')
        self.rp.save()
        self.xss_post = Post(title='example xss post', body=self.xss_str,
                             body_markup_type='markdown', comment=self.xss_str)
        self.xss_post.save()

    def test_verbose_name(self):
        self.assertEquals(self.mp._meta.get_field('body').verbose_name, 'body of post')

    def test_markup_body(self):
        self.assertEquals(self.mp.body.raw, '**markdown**')
        self.assertEquals(self.mp.body.rendered, '<p><strong>markdown</strong></p>')
        self.assertEquals(self.mp.body.markup_type, 'markdown')

    def test_markup_unicode(self):
        u = unicode(self.rp.body.rendered)
        self.assertEquals(u, u'<p><em>ReST</em></p>\n')

    def test_from_database(self):
        " Test that data loads back from the database correctly and 'post' has the right type."
        p1 = Post.objects.get(pk=self.mp.pk)
        self.assert_(isinstance(p1.body, Markup))
        self.assertEquals(unicode(p1.body), u'<p><strong>markdown</strong></p>')

    ## Assignment ##
    def test_body_assignment(self):
        self.rp.body = '**ReST**'
        self.rp.save()
        self.assertEquals(unicode(self.rp.body), u'<p><strong>ReST</strong></p>\n')

    def test_raw_assignment(self):
        self.rp.body.raw = '*ReST*'
        self.rp.save()
        self.assertEquals(unicode(self.rp.body), u'<p><em>ReST</em></p>\n')

    def test_rendered_assignment(self):
        def f():
            self.rp.body.rendered = 'this should fail'
        self.assertRaises(AttributeError, f)

    def test_body_type_assignment(self):
        self.rp.body.markup_type = 'markdown'
        self.rp.save()
        self.assertEquals(self.rp.body.markup_type, 'markdown')
        self.assertEquals(unicode(self.rp.body), u'<p><em>ReST</em></p>')

    ## Serialization ##

    def test_serialize_to_json(self):
        stream = serializers.serialize('json', Post.objects.all())
        self.assertEquals(stream, '[{"pk": 1, "model": "tests.post", "fields": {"body": "**markdown**", "comment": "", "_comment_rendered": "", "_body_rendered": "<p><strong>markdown</strong></p>", "title": "example markdown post", "comment_markup_type": "markdown", "body_markup_type": "markdown"}}, {"pk": 2, "model": "tests.post", "fields": {"body": "*ReST*", "comment": "", "_comment_rendered": "", "_body_rendered": "<p><em>ReST</em></p>\\n", "title": "example restructuredtext post", "comment_markup_type": "markdown", "body_markup_type": "ReST"}}, {"pk": 3, "model": "tests.post", "fields": {"body": "<script>alert(\'xss\');</script>", "comment": "<script>alert(\'xss\');</script>", "_comment_rendered": "<p>&lt;script&gt;alert(&#39;xss&#39;);&lt;/script&gt;</p>", "_body_rendered": "<script>alert(\'xss\');</script>", "title": "example xss post", "comment_markup_type": "markdown", "body_markup_type": "markdown"}}]')

    def test_deserialize_json(self):
        stream = serializers.serialize('json', Post.objects.all())
        obj = list(serializers.deserialize('json', stream))[0]
        self.assertEquals(obj.object, self.mp)

    ## Other ##

    def test_escape_html(self):
        # the rendered string has been escaped
        self.assertEquals(self.xss_post.comment.raw, self.xss_str)
        self.assertEquals(unicode(self.xss_post.comment.rendered), u'<p>&lt;script&gt;alert(&#39;xss&#39;);&lt;/script&gt;</p>')

    def test_escape_html_false(self):
        # both strings here are the xss_str, no escaping was done
        self.assertEquals(self.xss_post.body.raw, self.xss_str)
        self.assertEquals(unicode(self.xss_post.body.rendered), self.xss_str)

    def test_inheritance(self):
        # test that concrete correctly got the added fields
        concrete_fields = [f.name for f in Concrete._meta.fields]
        self.assertEquals(concrete_fields, ['id', 'content', 'content_markup_type', '_content_rendered'])

    def test_markup_type_validation(self):
        self.assertRaises(ValueError, MarkupField, 'verbose name', 'markup_field', 'bad_markup_type')

    def test_default_markup_types(self):
        from markupfield.markup import DEFAULT_MARKUP_TYPES
        for markup_type in DEFAULT_MARKUP_TYPES:
            rendered = markup_type[1](u'test')
            self.assertTrue(hasattr(rendered, '__str__'))

class MarkupWidgetTests(TestCase):
    def test_markuptextarea_render(self):
        a = Article(normal_field='**normal**', normal_field_markup_type='markdown',
                    default_field='**default**', markdown_field='**markdown**',
                    markup_choices_field_markup_type='nomarkup')
        a.save()
        af = ArticleForm(instance=a)
        self.assertEquals(unicode(af['normal_field']), u'<textarea id="id_normal_field" rows="10" cols="40" name="normal_field">**normal**</textarea>')

    def test_no_markup_type_field_if_set(self):
        'ensure that a field with non-editable markup_type set does not have a _markup_type field'
        self.assert_('markdown_field_markup_type' not in ArticleForm().fields.keys())

    def test_markup_type_choices(self):
        self.assertEquals(ArticleForm().fields['normal_field_markup_type'].choices,
                          [('markdown', 'markdown'), ('ReST', 'ReST')])
        self.assertEquals(ArticleForm().fields['markup_choices_field_markup_type'].choices,
                          [('pandamarkup', 'pandamarkup'), ('nomarkup', 'nomarkup')])

    def test_default_markup_type(self):
        self.assert_(ArticleForm().fields['normal_field_markup_type'].initial is None)
        self.assertEqual(ArticleForm().fields['default_field_markup_type'].initial, 'markdown')
