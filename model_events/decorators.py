from model_events import constants
from model_events.constants import RELATED_CHANGES
from model_events.exceptions import IllegalArgumentError


class InnerEventDecorator:
    def __init__(self, func, event_type, valid_args, *args, **kwargs):
        self.valid_args = valid_args
        self.fields = kwargs.pop('fields', None)
        self.field = kwargs.pop('field', None)
        self.prev = kwargs.pop('prev', None)
        self.new = kwargs.pop('new', None)

        self._validate_decorator_args()
        self.check_trigger_function = self._get_trigger_check_function()

        self.event_type = event_type
        self.func = func
        self.is_related_event = event_type in RELATED_CHANGES

    def __set_name__(self, owner, name):
        event = self.event_type

        # To avoid having a single event_types version in the subclasses
        if owner.event_types == {}:
            owner.event_types = {}

        event_type_list = owner.event_types.get(event)

        if event_type_list:
            event_type_list.add(name)
        else:
            event_type_list = {name}

        owner.event_types[event] = event_type_list

    def __call__(self, func_self, *args, **kwargs):
        changed_related_field = kwargs.pop('_change_related', None)

        do_trigger = self.check_trigger_function(func_self, changed_related_field=changed_related_field)
        if not do_trigger:
            return
        return self.func(func_self, *args, **kwargs)

    def _no_arg_check_trigger_function(self, outer_ref, *args, **kwargs):
        return True

    def _fields_arg_check_trigger_function(self, outer_self, *args, **kwargs):
        changed_related_field = kwargs.pop('changed_related_field', None)

        if changed_related_field:
            changed_related_field = [changed_related_field]
        else:
            changed_related_field = []

        changed_fields = changed_related_field + list(outer_self.changed_fields)
        return set(self.fields) <= set(changed_fields)

    def _plain_field_arg_check_trigger_function(self, outer_self, *args, **kwargs):
        changed_related_field = kwargs.pop('changed_related_field', None)

        if changed_related_field:
            changed_related_field = [changed_related_field]
        else:
            changed_related_field = []

        changed_fields = changed_related_field + list(outer_self.changed_fields)
        return self.field in changed_fields

    def _field_arg_with_prev_check_trigger_function(self, outer_self, *args, **kwargs):
        trigger = False
        if self._plain_field_arg_check_trigger_function(outer_self):
            prev_value = outer_self.get_prev_value(self.field)
            if prev_value == self.prev:
                trigger = True

        return trigger

    def _field_arg_with_new_check_trigger_function(self, outer_self, *args, **kwargs):
        trigger = False
        if self._plain_field_arg_check_trigger_function(outer_self):
            new_val = outer_self.get_new_value(self.field)
            if new_val == self.new:
                trigger = True

        return trigger

    def _field_arg_with_new_and_prev_check_trigger_function(self, outer_self, *args, **kwargs):
        prev_ok = self._field_arg_with_prev_check_trigger_function(outer_self)
        new_ok = self._field_arg_with_new_check_trigger_function(outer_self)

        return prev_ok and new_ok

    def _get_trigger_check_function(self):
        passed_args = self._get_passed_arguments_str()

        if len(passed_args) == 0:
            check_trigger_function = self._no_arg_check_trigger_function
        elif 'fields' in passed_args:
            check_trigger_function = self._fields_arg_check_trigger_function
        elif 'field' in passed_args and 'prev' not in passed_args and 'new' not in passed_args:
            check_trigger_function = self._plain_field_arg_check_trigger_function
        elif 'field' in passed_args and 'prev' in passed_args and 'new' not in passed_args:
            check_trigger_function = self._field_arg_with_prev_check_trigger_function
        elif 'field' in passed_args and 'prev' not in passed_args and 'new' in passed_args:
            check_trigger_function = self._field_arg_with_new_check_trigger_function
        elif 'field' in passed_args and 'prev' in passed_args and 'new' in passed_args:
            check_trigger_function = self._field_arg_with_new_and_prev_check_trigger_function
        else:
            return IllegalArgumentError(
                "Can't find a triggerer for the passed arguments"
            )

        return check_trigger_function

    def _get_passed_arguments_str(self):
        passed_args = []
        for arg in ['field', 'fields', 'prev', 'new']:
            if getattr(self, arg, None) is not None:
                passed_args.append(arg)

        return passed_args

    def _validate_valid_args(self):
        if self.valid_args == '*':
            return

        passed_args = self._get_passed_arguments_str()

        if not (set(passed_args) <= set(self.valid_args)):
            raise IllegalArgumentError(
                f'Illegal argument is passed to the decorator, '
                f'allowed arguments are {self.valid_args}'
            )

    def _validate_multiple_fields(self):
        if self.fields and not (self.field is None and self.prev is None and self.new is None):
            raise IllegalArgumentError(
                'When field is passed as an argument, '
                'the fields prev and new should be None.'
            )

    def _validate_one_field(self):
        if self.field and self.fields is not None:
            raise IllegalArgumentError(
                'When field is passed as an argument, '
                'the fields should be None.'
            )

        if self.field is None and (self.prev is not None or self.new is not None):
            raise IllegalArgumentError(
                'When prev or new is passed as an argument, '
                'the field should not be None.'
            )

    def _validate_decorator_args(self):
        self._validate_valid_args()
        self._validate_multiple_fields()
        self._validate_one_field()


class InnerEventDecoratorFactory:
    event_type = None
    valid_args = '*'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, func):
        cls = self.__class__
        return InnerEventDecorator(func, cls.event_type, cls.valid_args, *self.args, **self.kwargs)


class PreCreateEvent(InnerEventDecoratorFactory):
    event_type = constants.PRE_CREATE
    valid_args = ['field', 'new']


class PostCreateEvent(InnerEventDecoratorFactory):
    event_type = constants.POST_CREATE
    valid_args = ['field', 'new']


class PreSaveEvent(InnerEventDecoratorFactory):
    event_type = constants.PRE_SAVE
    valid_args = '*'


class PostSaveEvent(InnerEventDecoratorFactory):
    event_type = constants.POST_SAVE
    valid_args = '*'


class PreDeleteEvent(InnerEventDecoratorFactory):
    event_type = constants.PRE_DELETE
    valid_args = []


class PostDeleteEvent(InnerEventDecoratorFactory):
    event_type = constants.POST_DELETE
    valid_args = []


class FKChangeEvent(InnerEventDecoratorFactory):
    event_type = constants.FK_CHANGE
    valid_args = '*'


class M2MChangeEvent(InnerEventDecoratorFactory):
    event_type = constants.M2M_CHANGE
    valid_args = '*'
