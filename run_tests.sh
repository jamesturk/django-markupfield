#!/bin/bash

args="--settings=markupfield.tests.settings --pythonpath=."

error=false
# testing for bug #20

# removing old, pyc files. Python will overwrite them if the file is updated but
# python won't remove them when a file has been removed. These old files can then
# be still imported, which often ends up in an error when testing migration.
find .. -name "*.pyc" -type f | xargs rm
rm -rf migrations markuptest.db

echo "> Testing migration..."
django-admin.py makemigrations tests $args || error=true
django-admin.py migrate $args || error=true

echo "> Unit testing"
django-admin.py test $args || error=true

echo "> Cleaning up..."
rm -r markupfield/tests/migrations
rm markuptest.db

if $error; then
    exit 1
else
    exit 0
fi

# django-admin.py test --settings=markupfield.tests.settings --pythonpath=../..
