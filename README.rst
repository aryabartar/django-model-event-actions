django-model-event-actions |latest-version|
===========================================
|python-support| |django-support| |pypi| |license|

.. start docs include

This package is a replacement for the builtin Django_ Signals which you can define all of the
events and actions in the model itself and add conditions to determine when they are triggered.
With the help of this package you can track the changed field previous and current values and
determine when an action should trigger by creating an event with the decorators in the model.

A simple example will be:

.. code-block:: python

    class User(EventActionModel):
        is_active = models.BooleanField()

        @PostSaveEvent(field='is_active', prev=False, now=True)
        def user_deactivated(self):
            # logic

        @PostCreateEvent()
        def post_create(self):
            # logic

.. end docs include



.. |latest-version| image:: https://img.shields.io/badge/version-1.1-green
   :alt: Latest version on PyPI
   :target: https://pypi.org/project/django-model-event-actions/
.. |python-support| image:: https://img.shields.io/badge/python-%2B3.6-blue
   :target: https://pypi.org/project/django-model-event-actions/
   :alt: Python version
.. |django-support| image:: https://img.shields.io/badge/django-%2B2.1-blue
   :target: https://pypi.org/project/django-model-event-actions/
   :alt: Django versions
.. |pypi| image:: https://img.shields.io/badge/pypi-1.1-blue
   :target: https://pypi.org/project/django-model-event-actions/
   :alt: Pypi link
.. |license| image:: https://img.shields.io/badge/license-MIT-green
   :alt: Software license
   :target: https://github.com/aryabartar/django-model-event-actions/blob/master/LICENSE
.. _`Django`: http://www.djangoproject.com/



Installation
++++++++++++

.. start installation include

Get the package from pypi::

    $ pip install django-model-event-actions

Subclass the models:

.. code-block:: python

    from django_model_event_actions.models import EventActionModel

    class MyClass(EventActionModel):
        ...


Add the event decorator:

.. code-block:: python

    from django_model_event_actions.models import EventActionModel

    class MyClass(EventActionModel):
        name = models.CharField()

        @PostCreateEvent(field='name'):
        def my_handler(self):
            # logic

.. end installation include


Tutorial
++++++++

To start using the package take a look at the documentation_ in readthedocs.

.. _`documentation`: http://www.djangoproject.com/
