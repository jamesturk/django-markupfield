
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'markuptest.db'

import markdown
from docutils.core import publish_parts

def render_rest(markup):
    parts = publish_parts(source=markup, writer_name="html4css1")
    return parts["fragment"]

MARKUP_FIELD_TYPES = {
    'markdown': markdown.markdown,
    'ReST': render_rest,
}

INSTALLED_APPS = (
    'markupfield.tests',
)
