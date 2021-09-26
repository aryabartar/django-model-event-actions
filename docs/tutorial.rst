========
Tutorial
========

This tutorial will show you how to work with django-model-event-actions package
and gives you an idea of why using this package over default `Django Signals`_ will
result in lower codes and a cleaner design and show you the extra functionalities
that are not included in the Signals.

Please note that request_started_ and request_finished_ are not supported since they
are not a part of django models and we encourage you using Signals for that.

.. _Django Signals: https://docs.djangoproject.com/en/3.2/topics/signals/
.. _request_started:: https://docs.djangoproject.com/en/3.2/ref/signals/#django.core.signals.request_started/
.. _request_finished:: https://docs.djangoproject.com/en/3.2/ref/signals/#django.core.signals.request_finished


Comparison with Signals
==========

Imagine we have a Customer model and we want to send an email when the customer is created.

.. code-block:: python

    # models.py

    class Customer(models.Model):
        email = models.EmailField()


The signals way will be:

.. code-block:: python

    # email.py

    @receiver(post_init, sender=Customer)
    def send_creation_email(sender, instance, created, **kwargs):
        if created:
            # sending email logic



The django_model_events will be:

.. code-block:: python

    # models.py

    class Customer(models.Model):
        email = models.EmailField()

    @PreCreateEvent()
    def send_creation_email(self):
        # sending email logic

This gives you a idea about how to use this package but we will cover the use cases where
this package will come so handy and useful as we go through the document.

.. list-table:: Signals Replacement
   :widths: 25 35 40
   :header-rows: 1

   * - Event Decorator
     - Signal
     - Event Arguments
   * - PreCreateEvent
     - pre_save (needs explicit check)
     - ['field', 'new']
   * - PostCreateEvent
     - post_save (needs explict check)
     - ['field', 'new']
   * - PreSaveEvent
     - pre_save
     - ['fields', 'field', 'prev', 'new']
   * - PostSaveEvent
     - post_save
     - ['fields', 'field', 'prev', 'new']
   * - PreDeleteEvent
     - pre_delete
     - _
   * - PostDeleteEvent
     - post_delete
     - _
   * - FKChangeEvent
     - _
     - ['field']
   * - M2MChangeEvent
     - m2m_changed
     - ['field']


Arguments
=========
You can pass some attributes to the Event decorator to determine when the Event should trigger.

.. list-table:: Events Arguments
   :widths: 25 75
   :header-rows: 1

   * - Argument
     - Trigger Condition
   * - fields
     - Triggers if the listed 'fields' is a subset of the changed fields
   * - field
     - Triggers if the field is changed
   * - prev
     - Triggers if the previous value of the field was equal to 'prev'
   * - field
     - Triggers if the new value of the field is equal to 'prev'




You can use a combination of the arguments like this:

- Event()
- Event('fields'=['field_name_1', 'field_name_2', ...])
- Event('field'='field_name')
- Event('field'='field_name', prev='field_prev_value')
- Event('field'='field_name', new='field_new_value')
- Event('field'='field_name', prev='field_prev_value', new='field_new_value')


How to use
==========
Subclass EventActionModel rather than Django's models.Model for every model that you want
to use event actions for. The decorator's class shows the event's name and condition to be triggered
and the wrapped function is the callback function.
To make a function an action, add an Event decorator for that function in the model.

.. code-block:: python

    from event_actions.models import EventActionModel

    class Comment(EventActionModel):
        message = models.CharField()

        @PostSaveEvent(field='message')
        def log_message_changed(self):
            # logging logic

Decorators
==========

PreCreateEvent
++++++++++++++
PreCreateEvent will be triggered before the model's save method is called when a new object is created.

PreCreateEvent accepts ``field``, ``new`` arguments.

PostCreateEvent
+++++++++++++++
PostCreateEvent will be triggered after the model's save method is called when a new object is created.

PreCreateEvent accepts ``field``, ``new`` arguments.

PreSaveEvent
++++++++++++
PreSaveEvent will be triggered before the model's save method, this event will not be triggered
when the model is created.

PreSaveEvent accepts ``fields``, ``field``, ``prev`` and ``new`` arguments.

PostSaveEvent
+++++++++++++
PostSaveEvent will be triggered after the model's save method, this event will not be triggered
when the model is created.

PostSaveEvent accepts ``fields``, ``field``, ``prev`` and ``new`` arguments.


PreDeleteEvent
++++++++++++++
PreDeleteEvent will be triggered before the model's delete method.

PreDeleteEvent does not accept any argument.


PostDeleteEvent
+++++++++++++++
PostDeleteEvent will be triggered after the model's delete method.

PostDeleteEvent does not accept any argument.

FKChangeEvent
+++++++++++++
FKChangeEvent will be triggered if any value of the pointed instance by the FK field is changed.
The foreign key's model should subclass EventActionModel also.

PostDeleteEvent should have the ``field`` arguments.

.. code-block:: python

    class User(EventActionModel):
        # User fields

    # This won't be tracked because it's not subclassing EventActionModel
    class Post(models.Model):
        # Post fields

    class Comment(EventActionModel):
        author = models.ForeignKey(User)
        post = models.ForeignKey(Post)

        @FKChangeEvent(field='author') # this will work
        def author_changed(self):
            # logic

        @FKChangeEvent(field='post') # this won't work
        def post_changed(self):
            # logic

Models
=================

EventActionModel
++++++++++++++++

This class uses the EventActionModelMixin and ModelDiffMixin mixin and subclasses Django's models.Model.




