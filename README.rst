==================
django-markupfield
==================

An implementation of MarkupField for Django

TODO:
 * validate markup_type options
 * write documentation
 * convert tests from doctest to unittest

Origin
======

For those coming here via django snippets or the tracker, my original implementation is at https://gist.github.com/67724/3b7497713897fa0021d58e46380e4d80626b6da2

Jacob Kaplan-Moss commented on twitter that he'd possibly like to see a MarkupField in core and I filed a ticket on the Django trac http://code.djangoproject.com/ticket/10317

The resulting django-dev discussion drastically changed the purpose of the field.  While I initially intended to write a version that seemed more acceptable for Django core I wound up feeling that the 'acceptable' version had so little functionality and so much complexity it wasn't worth using.

