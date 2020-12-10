==================
django-markupfield
==================

.. image:: https://github.com/jamesturk/django-markupfield/workflows/Test/badge.svg

.. image:: https://img.shields.io/pypi/v/django-markupfield.svg
    :target: https://pypi.python.org/pypi/django-markupfield

An implementation of a custom MarkupField for Django.  A MarkupField is in 
essence a TextField with an associated markup type.  The field also caches
its rendered value on the assumption that disk space is cheaper than CPU 
cycles in a web application.

Installation
============

The recommended way to install django-markupfield is with
`pip <https://pypi.python.org/pypi/pip>`_

It is not necessary to add ``'markupfield'`` to your ``INSTALLED_APPS``, it
merely needs to be on your ``PYTHONPATH``. However, to use titled markup you
either add ``'markupfield'`` to your ``INSTALLED_APPS`` or add the
corresponding translations to your project translation.

Requirements
------------

Requires Django >= 2.2 and 3.6+

* 1.5.x is the last release to officially support Django < 2.2 or Python 2.7
* 1.4.x is the last release to officially support Django < 1.11
* 1.3.x is the last release to officially support Django 1.4 or Python 3.3

Settings
========

To best make use of MarkupField you should define the
``MARKUP_FIELD_TYPES`` setting, a mapping of strings to callables that
'render' a markup type::

    import markdown
    from docutils.core import publish_parts

    def render_rest(markup):
        parts = publish_parts(source=markup, writer_name="html4css1")
        return parts["fragment"]

    MARKUP_FIELD_TYPES = (
        ('markdown', markdown.markdown),
        ('ReST', render_rest),
    )

If you do not define a ``MARKUP_FIELD_TYPES`` then one is provided with the
following markup types available:

html:
    allows HTML, potentially unsafe
plain:
    plain text markup, calls urlize and replaces text with linebreaks
markdown:
    default `markdown`_ renderer (only if `markdown`_ is installed)
restructuredtext:
    default `ReST`_ renderer (only if `docutils`_ is installed)

It is also possible to override ``MARKUP_FIELD_TYPES`` on a per-field basis
by passing the ``markup_choices`` option to a ``MarkupField`` in your model
declaration.

.. _`ReST`: http://docutils.sourceforge.net/rst.html
.. _`markdown`: https://pypi.python.org/pypi/Markdown
.. _`docutils`: http://docutils.sourceforge.net/

Usage
=====

Using MarkupField is relatively easy, it can be used in any model definition::

    from django.db import models
    from markupfield.fields import MarkupField

    class Article(models.Model):
        title = models.CharField(max_length=100)
        slug = models.SlugField(max_length=100)
        body = MarkupField()

``Article`` objects can then be created with any markup type defined in
``MARKUP_FIELD_TYPES``::

    Article.objects.create(title='some article', slug='some-article',
                           body='*fancy*', body_markup_type='markdown')

You will notice that a field named ``body_markup_type`` exists that you did
not declare, MarkupField actually creates two extra fields here 
``body_markup_type`` and ``_body_rendered``.  These fields are always named
according to the name of the declared ``MarkupField``.

Arguments
---------

``MarkupField`` also takes three optional arguments.  Either
``default_markup_type`` and ``markup_type`` arguments may be specified but
not both.

``default_markup_type``:
    Set a markup_type that the field will default to if one is not specified.
    It is still possible to edit the markup type attribute and it will appear
    by default in ModelForms.

``markup_type``:
    Set markup type that the field will always use, ``editable=False`` is set
    on the hidden field so it is not shown in ModelForms.

``markup_choices``:
    A replacement list of markup choices to be used in lieu of
    ``MARKUP_FIELD_TYPES`` on a per-field basis.

``escape_html``:
    A flag (False by default) indicating that the input should be regarded
    as untrusted and as such will be run through Django's ``escape`` filter.


Examples
~~~~~~~~

``MarkupField`` that will default to using markdown but allow the user a choice::

    MarkupField(default_markup_type='markdown')

``MarkupField`` that will use ReST and not provide a choice on forms::

    MarkupField(markup_type='restructuredtext')

``MarkupField`` that will use a custom set of renderers::

    CUSTOM_RENDERERS = (
        ('markdown', markdown.markdown),
        ('wiki', my_wiki_render_func)
    )
    MarkupField(markup_choices=CUSTOM_RENDERERS)

.. note::
    When using ``markdown``, be sure to use ``markdown.markdown`` and not
    the ``markdown.Markdown`` class, the class requires an explicit ``reset``
    to function properly in some cases.  (See [issue #40](https://github.com/jamesturk/django-markupfield/issues/40)
    for details.)


Accessing a MarkupField on a model
----------------------------------

When accessing an attribute of a model that was declared as a ``MarkupField``
a special ``Markup`` object is returned.  The ``Markup`` object has three
parameters:

``raw``:
    The unrendered markup.
``markup_type``:
    The markup type.
``rendered``:
    The rendered HTML version of ``raw``, this attribute is read-only.

This object has a ``__unicode__`` method that calls
``django.utils.safestring.mark_safe`` on ``rendered`` allowing MarkupField
objects to appear in templates as their rendered selfs without any template
tag or having to access ``rendered`` directly.

Assuming the ``Article`` model above::

    >>> a = Article.objects.all()[0]
    >>> a.body.raw
    u'*fancy*'
    >>> a.body.markup_type
    u'markdown'
    >>> a.body.rendered
    u'<p><em>fancy</em></p>'
    >>> print unicode(a.body)
    <p><em>fancy</em></p>

Assignment to ``a.body`` is equivalent to assignment to ``a.body.raw`` and
assignment to ``a.body_markup_type`` is equivalent to assignment to 
``a.body.markup_type``.

.. important::
    Keeping in mind that ``body`` is MarkupField instance is particullary important with ``default`` or ``default_if_none`` filter for model that could be blank. If ``body``'s ``rendered`` is ``None`` or empty string (``""``) these filters will *not* evaluate ``body`` as falsy to display default text::
    
        {{ a.body|default:"<missing body>" }}
    
    That's because ``body`` is regular non-``None`` MarkupField instance. To let ``default`` or ``default_if_none`` filters to work evaluate ``rendered`` MarkupField attribute instead. To prevent escaping HTML for the case ``rendered`` is truethy, finish chain with ``safe`` filter::
    
        {{ a.body.rendered|default:"<missing body>"|safe }} 

.. note::
    a.body.rendered is only updated when a.save() is called

