from django.db import models

from .mixins import ModelDiffMixin, EventActionModelMixin


class EventActionModel(EventActionModelMixin, ModelDiffMixin, models.Model):
    event_types = {}

    class Meta:
        abstract = True
