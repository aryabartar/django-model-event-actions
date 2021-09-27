from django.db.models import ManyToOneRel
from django.forms import model_to_dict

from . import constants
from event_actions.constants import FK_CHANGE


class ModelDiffMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        """
        Return initial and second value of a field if changed.
        :return: A dictionary in the format:
                     {'changed_field_1': ('initial_value', 'new_value'), 'changed_field_2' ... }
        """
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        """Return the objects values are changed or not"""
        return bool(self.diff)

    @property
    def changed_fields(self):
        """Return changed fields in an array: [f1, f2, ...]"""
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """Return a diff for field if it's changed and None otherwise."""
        return self.diff.get(field_name, None)

    def get_prev_value(self, field_name):
        return self.get_field_diff(field_name)[0]

    def get_new_value(self, field_name):
        return self.get_field_diff(field_name)[1]

    def save(self, *args, **kwargs):
        """Saves model and set initial state."""
        super().save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in
                                           self._meta.fields])


class EventActionModelMixin:
    def save(self, *args, **kwargs):
        new_instance = self._state.adding

        if new_instance:
            self._call_actions(constants.PRE_CREATE)
        else:
            self._call_actions(constants.PRE_SAVE)

        instance = super().save(*args, **kwargs)

        if new_instance:
            self._call_actions(constants.POST_CREATE)
        else:
            self._call_actions(constants.POST_SAVE)

        self._call_related_objs()

        return instance

    def delete(self, *args, **kwargs):
        self._call_actions(constants.PRE_DELETE)
        ret = super().delete(*args, **kwargs)
        self._call_actions(constants.POST_DELETE)

        return ret

    def _call_related_objs(self):
        fk_relations = self._get_reverse_fields()

        for fk in fk_relations:
            related_objs = fk.related_model.objects.filter(**{fk.remote_field.name: self.id})
            for obj in related_objs:
                obj._fk_changed(fk.remote_field.name)

    def _get_reverse_fields(self):
        fields = self._meta.get_fields()
        fk_relations = [f for f in fields if isinstance(f, ManyToOneRel)]
        return fk_relations

    @classmethod
    def _get_action_functions_name(cls, event_type):
        actions = cls.event_types.get(event_type, [])
        return actions

    def _get_callable_functions(self, function_names):
        callable_functions = [getattr(self, func_name) for func_name in function_names]
        return callable_functions

    def _call_function(self, function, *args, **kwargs):
        return function(*args, **kwargs)

    def _call_actions(self, event_type, *args, **kwargs):
        function_names = self.__class__._get_action_functions_name(event_type)
        functions = self._get_callable_functions(function_names)

        for func in functions:
            self._call_function(func, self, *args, **kwargs)

    def _fk_changed(self, changed_field):
        self._call_actions(FK_CHANGE, _change_related=changed_field)
