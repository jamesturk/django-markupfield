from distutils.core import setup

long_description = open('README.rst').read()

setup(
    name='django-markupfield',
    version="1.0.0a2",
    package_dir={'markupfield': 'markupfield'},
    packages=['markupfield', 'markupfield.tests'],
    description='Custom Django field for easy use of markup in text fields',
    author='James Turk',
    author_email='james.p.turk@gmail.com',
    license='BSD License',
    url='http://github.com/jamesturk/django-markupfield/',
    long_description=long_description,
    platforms=["any"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Environment :: Web Environment',
    ],
)
