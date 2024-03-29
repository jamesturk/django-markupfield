2.0.1 - 25 October 2021
=======================
    - updates for removal of function aliases in Django 4.0

2.0.0 - 8 January 2020
======================
  - drop Python 2 support
  - support for Django 2.2 and 3.0
  - added __bool__ method to Markup, allows for |default to work in templates
    as expected (fixes #53)

1.5.1 - 10 January 2019
=======================
    - fix for MarkupField in list_display in Django 2.1

1.5.0 - 16 August 2018
======================
    - add support for Wagtail search
    - drop support for Django <= 1.10
    - add support for custom renderer param (fixes Django 2.1 support)

1.4.3 - 2 October 2017
======================
    - remove deprecated call to _get_val_from_obj (fix for Django 2.0)

1.4.2 - 4 April 2017
====================
    - copy default to field

1.4.1 - 6 October 2016
======================
    - compatibility tweaks for Django 1.9 and 1.10

1.4.0 - 17 December 2015
=========================
    - bugfixes for Django 1.9
	- drop support for deprecated Django versions

1.3.5 - 21 May 2015
===================
    - properly handle null=True

1.3.4 - 29 April 2015
=====================
    - Fix for an issue where __proxy__ objects interfere w/ widget rendering.

1.3.3 - 21 April 2015
=====================
    - Add test for issue fixed in last release: https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2015-0846
      Further documented here: https://www.djangoproject.com/weblog/2015/apr/21/docutils-security-advisory/

1.3.2 - 16 April 2015
=====================
    - Fix for an issue with ReST, thanks to Markus Holtermann

1.3.1 - 15 April 2015
=====================
    - Fix translation support to be lazy, thanks to Michael Kutý

1.3.0 - 22 February 2015
========================
    - Django 1.7 migration support, thanks to Frank Wiles
    - dedicated option for titles in markup choice field thanks to Markus Holtermann
    - fix for latest version of markdown library

1.2.1 - 10 July 2014
====================
    - value_to_string check, fixing #16
    - urllize & linebreak fix, fixing #18
    - fix for __unicode__, fixing #9

1.2.0 - 22 July 2013
====================
    - drop support for markup_choices being a dict entirely
    - PEP8 compliance
    - bugfix for default 'plain' markup type that escapes HTML

1.1.1 - 16 March 2013
=====================
    - experimental Python 3 support with Django 1.5
    - drop support for Django 1.3/Python 2.5
    - markup_choices can no longer be a dict (deprecated pre-1.0)

1.1.0 - bad release, ignore
=============================

1.0.2 - 25 March 2011
=====================
    - fix Django 1.3 DeprecationWarning

1.0.1 - 28 Feb 2011
===================
    - added a fix for MarkupField to work with South >= 0.7

1.0.0 - 1 Feb 2011
==================
    - added markup_choices option to MarkupField
    - switch to tuple/list for setting markup_type, dict deprecated
    - split markup detection into markupfield.markup
    - escape_html option

0.3.1 - January 28 2010
=======================
    - fix bug when adding a MarkupField to an abstract model (github issue #1)

0.3.0 - October 23 2009
=======================
    - enable pygments support by default if it is installed

0.2.0 - August 3 2009
=====================
    - fixed bug with using MarkupField widgets on postgres backend
    - correctly check markup_type when doing pre_save

0.1.2 - July 7 2009
===================
    - fixed bug with using MarkupField on postgres backend

0.1.0
=====
    - initial working release
