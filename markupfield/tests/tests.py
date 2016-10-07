from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from django.core import serializers
from django.utils.encoding import smart_text
from markupfield.markup import DEFAULT_MARKUP_TYPES
from markupfield.fields import MarkupField, Markup
from markupfield.widgets import MarkupTextarea, AdminMarkupTextareaWidget
from markupfield.tests.models import Post, Article, Concrete, NullTestModel, DefaultTestModel

from django.forms.models import modelform_factory
ArticleForm = modelform_factory(Article, fields=['normal_field', 'normal_field_markup_type',
                                                 'markup_choices_field',
                                                 'markup_choices_field_markup_type',
                                                 'default_field', 'default_field_markup_type',
                                                 'markdown_field'])


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
        self.plain_str = ('<span style="color: red">plain</span> post\n\n'
                          'http://example.com')
        self.pp = Post(title='example plain post', body=self.plain_str,
                       body_markup_type='plain', comment=self.plain_str,
                       comment_markup_type='plain')
        self.pp.save()

    def test_verbose_name(self):
        self.assertEqual(self.mp._meta.get_field('body').verbose_name,
                         'body of post')

    def test_markup_body(self):
        self.assertEqual(self.mp.body.raw, '**markdown**')
        self.assertEqual(self.mp.body.rendered,
                         '<p><strong>markdown</strong></p>')
        self.assertEqual(self.mp.body.markup_type, 'markdown')

    def test_markup_unicode(self):
        u = smart_text(self.rp.body.rendered)
        self.assertEqual(u, '<p><em>ReST</em></p>\n')

    def test_from_database(self):
        """ Test that data loads back from the database correctly and 'post'
        has the right type."""
        p1 = Post.objects.get(pk=self.mp.pk)
        self.assertTrue(isinstance(p1.body, Markup))
        self.assertEqual(smart_text(p1.body),
                         '<p><strong>markdown</strong></p>')

    # Assignment #########

    def test_body_assignment(self):
        self.rp.body = '**ReST**'
        self.rp.save()
        self.assertEqual(smart_text(self.rp.body),
                         '<p><strong>ReST</strong></p>\n')

    def test_raw_assignment(self):
        self.rp.body.raw = '*ReST*'
        self.rp.save()
        self.assertEqual(smart_text(self.rp.body), '<p><em>ReST</em></p>\n')

    def test_rendered_assignment(self):
        def f():
            self.rp.body.rendered = 'this should fail'
        self.assertRaises(AttributeError, f)

    def test_body_type_assignment(self):
        self.rp.body.markup_type = 'markdown'
        self.rp.save()
        self.assertEqual(self.rp.body.markup_type, 'markdown')
        self.assertEqual(smart_text(self.rp.body), '<p><em>ReST</em></p>')

    # Serialization ###########

    def test_serialize_to_json(self):
        stream = serializers.serialize('json', Post.objects.all()[:3])

        # Load the data back into Python so that a failed comparison gives a
        # better diff output.
        actual = json.loads(stream)
        expected = [
            {"pk": 1, "model": "tests.post",
             "fields": {"body": "**markdown**",
                        "comment": "",
                        "_comment_rendered": "",
                        "_body_rendered": "<p><strong>markdown</strong></p>",
                        "title": "example markdown post",
                        "comment_markup_type": "markdown",
                        "body_markup_type": "markdown"}},
            {"pk": 2, "model": "tests.post",
             "fields": {"body": "*ReST*",
                        "comment": "",
                        "_comment_rendered": "",
                        "_body_rendered": "<p><em>ReST</em></p>\n",
                        "title": "example restructuredtext post",
                        "comment_markup_type": "markdown",
                        "body_markup_type": "ReST"}},
            {"pk": 3, "model": "tests.post",
             "fields": {"body": "<script>alert(\'xss\');</script>",
                        "comment": "<script>alert(\'xss\');</script>",
                        "_comment_rendered": (
                            "<p>&lt;script&gt;alert("
                            "&#39;xss&#39;);&lt;/script&gt;</p>"),
                        "_body_rendered": "<script>alert(\'xss\');</script>",
                        "title": "example xss post",
                        "comment_markup_type": "markdown",
                        "body_markup_type": "markdown"}},
            #{"pk": 4, "model": "tests.post",
            # "fields": {"body": ('<span style="color: red">plain</span> '
            #                     'post\n\nhttp://example.com'),
            #            "comment": ('<span style="color: red">plain</span> '
            #                        'post\n\nhttp://example.com'),
            #            "_comment_rendered": (
            #                '<p>&amp;lt;span style=&amp;quot;color: red'
            #                '&amp;quot;&amp;gt;plain&amp;lt;/span&amp;gt; '
            #                'post</p>\n\n<p>http://example.com</p>'),
            #            "_body_rendered": ('<p>&lt;span style=&quot;color: '
            #                               'red&quot;&gt;plain&lt;/span&gt; '
            #                               'post</p>\n\n<p>http://example.com'
            #                               '</p>'),
            #            "title": "example plain post",
            #            "comment_markup_type": "plain",
            #            "body_markup_type": "plain"}},
        ]
        self.assertEqual(len(expected), len(actual))
        for n, item in enumerate(expected):
            self.maxDiff = None
            self.assertEqual(item['fields'], actual[n]['fields'])

    def test_deserialize_json(self):
        stream = serializers.serialize('json', Post.objects.all())
        obj = list(serializers.deserialize('json', stream))[0]
        self.assertEqual(obj.object, self.mp)

    def test_value_to_string(self):
        """
        Ensure field converts to string during _meta access

        Other libraries (Django REST framework, etc) go directly to the
        field layer to serialize, which can cause a "unicode object has no
        property called 'raw'" error. This tests the bugfix.
        """
        obj = self.rp
        field = self.rp._meta.get_field('body')
        self.assertNotEqual(field.value_to_string(obj), u'')    # expected
        self.assertEqual(field.value_to_string(None), u'')      # edge case

    # Other #################

    def test_escape_html(self):
        # the rendered string has been escaped
        self.assertEqual(self.xss_post.comment.raw, self.xss_str)
        self.assertEqual(
            smart_text(self.xss_post.comment.rendered),
            '<p>&lt;script&gt;alert(&#39;xss&#39;);&lt;/script&gt;</p>')

    def test_escape_html_false(self):
        # both strings here are the xss_str, no escaping was done
        self.assertEqual(self.xss_post.body.raw, self.xss_str)
        self.assertEqual(smart_text(self.xss_post.body.rendered), self.xss_str)

    def test_inheritance(self):
        # test that concrete correctly got the added fields
        concrete_fields = [f.name for f in Concrete._meta.fields]
        self.assertEqual(concrete_fields, ['id', 'content',
                                           'content_markup_type',
                                           '_content_rendered'])

    def test_markup_type_validation(self):
        self.assertRaises(ValueError, MarkupField, 'verbose name',
                          'markup_field', 'bad_markup_type')

    def test_default_markup_types(self):
        for markup_type in DEFAULT_MARKUP_TYPES:
            rendered = markup_type[1]('test')
            self.assertTrue(hasattr(rendered, '__str__'))

    def test_plain_markup_urlize(self):
        for key, func, _ in DEFAULT_MARKUP_TYPES:
            if key != 'plain':
                continue
            txt1 = 'http://example.com some text'
            txt2 = 'Some http://example.com text'
            txt3 = 'Some text http://example.com'
            txt4 = 'http://example.com. some text'
            txt5 = 'Some http://example.com. text'
            txt6 = 'Some text http://example.com.'
            txt7 = '.http://example.com some text'
            txt8 = 'Some .http://example.com text'
            txt9 = 'Some text .http://example.com'
            self.assertEqual(
                func(txt1),
                '<p><a href="http://example.com">http://example.com</a> some text</p>')
            self.assertEqual(
                func(txt2),
                '<p>Some <a href="http://example.com">http://example.com</a> text</p>')
            self.assertEqual(
                func(txt3),
                '<p>Some text <a href="http://example.com">http://example.com</a></p>')
            self.assertEqual(
                func(txt4),
                '<p><a href="http://example.com">http://example.com</a>. some text</p>')
            self.assertEqual(
                func(txt5),
                '<p>Some <a href="http://example.com">http://example.com</a>. text</p>')
            self.assertEqual(
                func(txt6),
                '<p>Some text <a href="http://example.com">http://example.com</a>.</p>')
            self.assertEqual(func(txt7), '<p>.http://example.com some text</p>')
            self.assertEqual(func(txt8), '<p>Some .http://example.com text</p>')
            self.assertEqual(func(txt9), '<p>Some text .http://example.com</p>')
            break


class MarkupWidgetTests(TestCase):

    def test_markuptextarea_used(self):
        self.assertTrue(isinstance(MarkupField().formfield().widget,
                                   MarkupTextarea))
        self.assertTrue(isinstance(ArticleForm()['normal_field'].field.widget,
                                   MarkupTextarea))

    def test_markuptextarea_render(self):
        if django.VERSION < (1, 10):
            expected = ('<textarea id="id_normal_field" rows="10" cols="40" '
                        'name="normal_field">**normal**</textarea>'
                        )
        else:
            expected = ('<textarea id="id_normal_field" required rows="10" cols="40" '
                        'name="normal_field">**normal**</textarea>'
                        )
        a = Article(normal_field='**normal**',
                    normal_field_markup_type='markdown',
                    default_field='**default**',
                    markdown_field='**markdown**',
                    markup_choices_field_markup_type='nomarkup')
        a.save()
        af = ArticleForm(instance=a)
        self.assertHTMLEqual(smart_text(af['normal_field']), expected)

    def test_no_markup_type_field_if_set(self):
        """ensure that a field with non-editable markup_type set does not
        have a _markup_type field"""
        self.assertTrue('markdown_field_markup_type' not in
                        ArticleForm().fields.keys())

    def test_markup_type_choices(self):
        # This function primarily tests the choices available to the widget.
        # By introducing titled markups (as third element in the markup_choices
        # tuples), this function also shows the backwards compatibility to the
        # old 2-tuple style and, by checking for the title of the 'fancy'
        # markup in the second test, also for the correkt title to the widget
        # choices.
        self.assertEqual(
            ArticleForm().fields['normal_field_markup_type'].choices,
            [('', '--'), ('markdown', 'markdown'), ('ReST', 'ReST'),
             ('plain', 'plain')])
        self.assertEqual(
            ArticleForm().fields['markup_choices_field_markup_type'].choices,
            [('', '--'), ('pandamarkup', 'pandamarkup'),
             ('nomarkup', 'nomarkup'), ('fancy', 'Some fancy Markup')])

    def test_default_markup_type(self):
        self.assertTrue(
            ArticleForm().fields['normal_field_markup_type'].initial is None)
        self.assertEqual(
            ArticleForm().fields['default_field_markup_type'].initial,
            'markdown')

    def test_model_admin_field(self):
        # borrows from regressiontests/admin_widgets/tests.py
        from django.contrib import admin
        ma = admin.ModelAdmin(Post, admin.site)
        self.assertTrue(isinstance(ma.formfield_for_dbfield(
            Post._meta.get_field('body'), request=None).widget,
            AdminMarkupTextareaWidget,
        ))


class MarkupFieldFormSaveTests(TestCase):

    def setUp(self):
        self.data = {'title': 'example post', 'body': '**markdown**',
                     'body_markup_type': 'markdown'}
        self.form_class = modelform_factory(Post, fields=['title', 'body',
                                                          'body_markup_type'])

    def test_form_create(self):
        form = self.form_class(self.data)
        form.save()

        actual = Post.objects.get(title=self.data['title'])
        self.assertEquals(actual.body.raw, self.data['body'])

    def test_form_update(self):
        existing = Post.objects.create(title=self.data['title'], body=self.data['body'],
                                       body_markup_type='markdown')

        update = {'title': 'New title', 'body': '**different markdown**',
                  'body_markup_type': 'markdown',
                  }
        form = self.form_class(update, instance=existing)
        form.save()

        actual = Post.objects.get(title=update['title'])
        self.assertEquals(actual.body.raw, update['body'])


class MarkupFieldLocalFileTestCase(TestCase):
    def test_no_raw(self):
        for markup_opt in DEFAULT_MARKUP_TYPES:
            if markup_opt[0] == 'restructuredtext':
                render_rest = markup_opt[1]
        body = render_rest('.. raw:: html\n    :file: AUTHORS.txt')

        self.assertNotIn('James Turk', body)


class MarkupWidgetRenderTestCase(TestCase):
    def test_model_admin_render(self):
        from django.utils.translation import ugettext_lazy as _
        w = AdminMarkupTextareaWidget()
        assert w.render(_('body'), _('Body'))


class NullTestCase(TestCase):
    def test_default_null_save(self):
        m = NullTestModel()
        m.save()
        self.assertEqual(smart_text(m.text), '')
        self.assertIsNone(m.text.raw)
        self.assertIsNone(m.text.rendered)


class DefaultTestCase(TestCase):
    def test_default_text_save(self):
        m = DefaultTestModel()
        m.save()
        self.assertEqual(smart_text(m.text), "<p><strong>nice</strong></p>")

    def test_assign_none(self):
        m = DefaultTestModel()
        m.save()
        self.assertEqual(smart_text(m.text), "<p><strong>nice</strong></p>")
        m.text.raw = None
        m.save()
        self.assertEqual(smart_text(m.text), '')
        self.assertIsNone(m.text.raw)
        self.assertIsNone(m.text.rendered)
