===================
Plant UML generator
===================

.. image:: https://img.shields.io/pypi/l/django-model2puml
.. image:: https://img.shields.io/github/v/tag/sen-den/django-model2puml
.. image:: https://img.shields.io/github/last-commit/sen-den/django-model2puml
.. image:: https://img.shields.io/github/commit-activity/m/sen-den/django-model2puml
.. image:: https://img.shields.io/pypi/dm/django-model2puml

django-model2puml app is a generator of project models structure in
PlantUML class notation.

Quick start
-----------

1. Add "uml_generator" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'puml_generator',
        ...
    ]

2. Run django management command ``generate_puml`` like this ``./manage.py generate_puml``

Params::

    --file - output file
    --title - provide a title for diagram
    --add-help - add models docstrings to diagram
    --add-choices - add Choices description of fields to diagram
    --add-legend - include explanation of the symbols used
    --add-omitted-headers - add a header stub for omitted foreign app
    --omit-history - omit Historical* tables from django-simple-history
    --omit - specify apps to be omitted in diagram
    --include - specify apps to be included in diagram; other will be omitted
    --headers-only - use only model header and relations, omit fields list

3. Check generated PlantUML file!

``./manage.py generate_puml --file diagram.puml --include auth contenttypes --add-help --add-legend``

.. image:: https://raw.githubusercontent.com/sen-den/django-model2puml/master/samples/sample-diagram-1.png

Release notes
-------------

v0.2.1 (2022-06-05)
...................

- Refine README.rst

v0.2.0 (2022-04-17)
...................

- Add omit-history flag for omit `django-simple-history <https://pypi.org/project/django-simple-history/>`_ library models

v0.1.14 (2021-03-15)
....................

- Fix ImportError in utils.py

v0.1.13 (2020-10-17)
....................

- Add documentation to generator
- Limit docstrings length
- Fix choices generation issues

v0.1.12 (2020-10-15)
....................

- Use UTF-8 for saving output

v0.1.11 (2020-10-15)
....................

- Add headers-only flag to use only model header and relations, omit fields list in UML

*Releases earlier than v0.1.11 yanked due to significant settings issues and must not be used*
