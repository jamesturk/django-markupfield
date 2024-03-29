import os
import markdown
from django.utils.html import escape, linebreaks, urlize
from docutils.core import publish_parts

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

if os.environ.get("DB") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "test",
            "USER": "test",
            "PASSWORD": "test",
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }
    }
else:
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "markuptest.db"}
    }


def render_rest(markup):
    parts = publish_parts(source=markup, writer_name="html4css1")
    return parts["fragment"]


MARKUP_FIELD_TYPES = [
    ("markdown", markdown.markdown),
    ("ReST", render_rest),
    ("plain", lambda markup: urlize(linebreaks(escape(markup)))),
]

INSTALLED_APPS = ("markupfield.tests",)

SECRET_KEY = "sekrit"

MIDDLEWARE_CLASSES = ()

ROOT_URLCONF = ()
