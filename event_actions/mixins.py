from django.db.models import ManyToOneRel
from django.forms import model_to_dict

from event_actions.constants import FK_CHANGE
from . import constants


class ModelChangesMixin(object):
    """
    This class tracks the changed fields while the save() method of the model is called.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._initial_values = self._current_values()

    @property
    def changed_fields(self):
        """
        Return changed fields in an array: [field_1, field_2, ...]
        """
        return self.diff.keys()

    @property
    def diff(self):
        """
        Return initial and second value of a field if changed.
        :return: A dictionary in the format:
                     {'changed_field_1': ('prev_value', 'new_value'), 'changed_field_2' ... }
        """
        initial_values = self._initial_values
        current_values = self._current_values()

        diffs = {}
        for key, value in initial_values.items():
            if value != current_values[key]:
                diffs[key] = (value, current_values[key])

        return diffs

    def get_field_diff(self, field_name):
        """
        Return a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def get_prev_value(self, field_name):
        """
        Return the field's previous value.
        """
        return self.get_field_diff(field_name)[0]

    def get_new_value(self, field_name):
        """
        Return the field's new values.
        """
        return self.get_field_diff(field_name)[1]

    def save(self, *args, **kwargs):
        """
        Call model's default save method and set the __initial state
        """
        super().save(*args, **kwargs)
        self._initial_values = self._current_values()

    def _current_values(self):
        return model_to_dict(
            self, fields=[field.name for field in self._meta.fields]
        )


class EventActionMixin:
    """
    A class to call the event decorator and their handler functions.
    This class uses ModelChangesMixin to track the changes in the models.
    """

    def save(self, *args, **kwargs):
        """
        Replace model's default save method and call the appropriate actions.
        """
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
        """
        Replace model's default delete method and call the appropriate actions.
        """
        self._call_actions(constants.PRE_DELETE)

        ret = super().delete(*args, **kwargs)

        self._call_actions(constants.POST_DELETE)

        return ret

    def _call_related_objs(self):
        """
        If the object's field's values are changed, inform the objects that have related (FK or M2M)
        reference to this object.
        """
        fk_relations = self._get_reverse_fields()

        for fk in fk_relations:
            related_objs = fk.related_model.objects.filter(**{fk.remote_field.name: self.id})
            for obj in related_objs:
                obj._fk_changed(fk.remote_field.name)

    def _get_reverse_fields(self):
        """
        Return the fields from other models that have FK reference to the current model.
        """
        fields = self._meta.get_fields()
        fk_relations = [f for f in fields if isinstance(f, ManyToOneRel)]
        return fk_relations

    @classmethod
    def _get_action_functions_name(cls, event_type):
        """
        Return the name of the functions bound to certain events.
        """
        actions = cls.event_types.get(event_type, [])
        return actions

    def _get_callable_functions(self, function_names):
        """
        Get the function names and return their callables.
        """
        callable_functions = [getattr(self, func_name) for func_name in function_names]
        return callable_functions

    def _call_function(self, function, *args, **kwargs):
        """
        Call the function with given args and kwargs.
        """
        return function(*args, **kwargs)

    def _call_actions(self, event_type, *args, **kwargs):
        """
        Call the handler functions bound to 'event_type'.
        """
        function_names = self.__class__._get_action_functions_name(event_type)
        functions = self._get_callable_functions(function_names)

        for func in functions:
            self._call_function(func, self, *args, **kwargs)

    def _fk_changed(self, changed_field):
        """
        Call the actions for FK_CHANGE
        """
        self._call_actions(FK_CHANGE, _change_related=changed_field)
