from functools import partial
from django.utils.html import escape, linebreaks, urlize
from django.utils.translation import pgettext_lazy as _
from django.conf import settings

# build DEFAULT_MARKUP_TYPES
DEFAULT_MARKUP_TYPES = [
    ("html", lambda markup: markup, _("django-markupfield", "HTML")),
    (
        "plain",
        lambda markup: linebreaks(urlize(escape(markup))),
        _("django-markupfield", "Plain"),
    ),
]

try:
    import pygments  # noqa

    PYGMENTS_INSTALLED = True

    def _register_pygments_rst_directive():
        from docutils import nodes
        from docutils.parsers.rst import directives
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, TextLexer
        from pygments.formatters import HtmlFormatter

        DEFAULT = HtmlFormatter()
        VARIANTS = {
            "linenos": HtmlFormatter(linenos=True),
        }

        def pygments_directive(
            name,
            arguments,
            options,
            content,
            lineno,
            content_offset,
            block_text,
            state,
            state_machine,
        ):
            try:
                lexer = get_lexer_by_name(arguments[0])
            except ValueError:
                # no lexer found - use the text one instead of an exception
                lexer = TextLexer()
            formatter = options and VARIANTS[options.keys()[0]] or DEFAULT
            parsed = highlight(u"\n".join(content), lexer, formatter)
            return [nodes.raw("", parsed, format="html")]

        pygments_directive.arguments = (1, 0, 1)
        pygments_directive.content = 1
        directives.register_directive("code", pygments_directive)


except ImportError:
    PYGMENTS_INSTALLED = False

try:
    import markdown

    md_filter = markdown.markdown

    # try and replace if pygments & codehilite are available
    if PYGMENTS_INSTALLED:
        try:
            from markdown.extensions.codehilite import makeExtension  # noqa

            md_filter = partial(
                markdown.markdown, extensions=[makeExtension(css_class="highlight")]
            )
        except ImportError:
            pass

    # whichever markdown_filter was available
    DEFAULT_MARKUP_TYPES.append(
        ("markdown", md_filter, _("django-markupfield", "Markdown"))
    )

except ImportError:
    pass

try:
    from docutils.core import publish_parts

    if PYGMENTS_INSTALLED:
        _register_pygments_rst_directive()

    def render_rest(markup):
        overrides = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        overrides.update({"raw_enabled": False, "file_insertion_enabled": False})
        parts = publish_parts(
            source=markup, writer_name="html4css1", settings_overrides=overrides
        )
        return parts["fragment"]

    DEFAULT_MARKUP_TYPES.append(
        ("restructuredtext", render_rest, _("django-markupfield", "Restructured Text"))
    )
except ImportError:
    pass
