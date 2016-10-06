from setuptools import setup

long_description = open('README.rst').read()

setup(
    name='django-markupfield',
    version="1.4.1",
    package_dir={'markupfield': 'markupfield'},
    packages=['markupfield', 'markupfield.tests'],
    package_data={'markupfield': ['locale/*/*/*']},
    description='Custom Django field for easy use of markup in text fields',
    author='James Turk',
    author_email='james.p.turk@gmail.com',
    license='BSD License',
    url='http://github.com/jamesturk/django-markupfield/',
    long_description=long_description,
    platforms=["any"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Environment :: Web Environment',
    ],
)
