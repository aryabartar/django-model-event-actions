from django.db import models

from .mixins import ModelChangesMixin, EventActionMixin


class EventActionModel(EventActionMixin, ModelChangesMixin, models.Model):
    """
    This models subclasses default Django's Model class and also uses EventActionMixin and ModelChangesMixin
    to track the field changes and call certain events and actions.

    To use the event actions you have to subclass this model rather than the Django's default models.Model.
    """

    event_types = {}

    class Meta:
        abstract = True
