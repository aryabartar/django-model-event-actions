"""Decorators to use as events"""

from . import constants
from .exceptions import IllegalArgumentError


class InnerEventDecorator:
    """
    This class is actual decorator for the handler function.

    The class will decide when the event will trigger and if the event is triggered,
    calls the handler function.
    """

    def __init__(self, func, event_type, valid_args, **kwargs):
        """
        Instantiates the InnerEventDecorator

        :param func: the handler function
        :param event_type: the type of event defined in constants with string type
        :param valid_args: a iterable list of valid argument names or '*' to accept anything
        :param kwargs: a dict containing the decorator arguments
        """
        self.valid_args = valid_args
        self.fields = kwargs.pop('fields', None)
        self.field = kwargs.pop('field', None)
        self.prev = kwargs.pop('prev', None)
        self.new = kwargs.pop('new', None)

        self._validate_decorator_args()
        self.check_trigger_function = self._get_trigger_check_function()

        self.event_type = event_type
        self.func = func
        self.is_related_event = event_type in constants.RELATED_CHANGES

    def __set_name__(self, owner, name):
        """
        The method is automatically called when the class is being created.

        This method updates the caller class's (which is a EventActionModel subclass) event_types attribute.
        The event_types will be in the format of {'event_name': ['handler_function_1', ...], }
        """
        event = self.event_type

        # To avoid having a single event_types version in the subclasses
        # for more information check this:
        # https://www.toptal.com/python/python-class-attributes-an-overly-thorough-guide
        if owner.event_types == {}:
            owner.event_types = {}

        event_type_list = owner.event_types.get(event)

        if event_type_list:
            event_type_list.add(name)
        else:
            event_type_list = {name}

        owner.event_types[event] = event_type_list

    def __call__(self, func_self, *args, **kwargs):
        """
        When the class's instance is called, check and trigger the action if needed
        """
        changed_related_field = kwargs.pop('_change_related', None)

        do_trigger = self.check_trigger_function(func_self, changed_related_field=changed_related_field)
        if not do_trigger:
            return
        return self.func(func_self, *args, **kwargs)

    def _no_arg_check_trigger_function(self, outer_ref, *args, **kwargs):
        """
        A handler for the decorators with no argument.

        Always return true.
        """
        return True

    def _fields_arg_check_trigger_function(self, outer_self, *args, **kwargs):
        """
        A handler for the decorators with only 'fields' argument.

        Return True if all of the passed fields in 'fields' argument is changed,
        otherwise return False.
        """
        changed_related_field = kwargs.pop('changed_related_field', None)

        if changed_related_field:
            changed_related_field = [changed_related_field]
        else:
            changed_related_field = []

        changed_fields = changed_related_field + list(outer_self.changed_fields)
        return set(self.fields) <= set(changed_fields)

    def _plain_field_arg_check_trigger_function(self, outer_self, *args, **kwargs):
        """
        A handler for the decorators with only 'field' argument.

        Return True if the passed field in 'field' argument is changed,
        otherwise return False.
        """
        changed_related_field = kwargs.pop('changed_related_field', None)

        if changed_related_field:
            changed_related_field = [changed_related_field]
        else:
            changed_related_field = []

        changed_fields = changed_related_field + list(outer_self.changed_fields)
        return self.field in changed_fields

    def _field_arg_with_prev_check_trigger_function(self, outer_self, *args, **kwargs):
        """
        A handler for the decorators with 'field' and 'prev' argument.

        Return True if the 'field' value is changed and also previous 'field' value was equal to 'prev',
        otherwise return False.
        """
        trigger = False
        if self._plain_field_arg_check_trigger_function(outer_self):
            prev_value = outer_self.get_prev_value(self.field)
            if prev_value == self.prev:
                trigger = True

        return trigger

    def _field_arg_with_new_check_trigger_function(self, outer_self, *args, **kwargs):
        """
        A handler for the decorators with 'field' and 'new' argument.

        Return True if the 'field's value is changed and also 'field's new value is equal to 'new',
        otherwise return False.
        """
        trigger = False
        if self._plain_field_arg_check_trigger_function(outer_self):
            new_val = outer_self.get_new_value(self.field)
            if new_val == self.new:
                trigger = True

        return trigger

    def _field_arg_with_new_and_prev_check_trigger_function(self, outer_self, *args, **kwargs):
        """
        A handler for the decorators with 'field', 'prev' and 'new' argument.

        Return True if the 'field's value is changed from 'prev' to 'new',
        otherwise return False.
        """
        prev_ok = self._field_arg_with_prev_check_trigger_function(outer_self)
        new_ok = self._field_arg_with_new_check_trigger_function(outer_self)

        return prev_ok and new_ok

    def _get_trigger_check_function(self):
        """
        Return the trigger checker function based on passed arguments to the decorator.
        """
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
        """
        Return passed arguments to the decorator
        """
        passed_args = []
        for arg in ['field', 'fields', 'prev', 'new']:
            # TODO: It will fail if the 'prev's actual value is None
            if getattr(self, arg, None) is not None:
                passed_args.append(arg)

        return passed_args

    def _validate_valid_args(self):
        """
        Check that passed arguments to the decorator is valid based on that decorator's valid_args.
        If not raise IllegalArgumentError.
        """
        if self.valid_args == '*':
            return

        passed_args = self._get_passed_arguments_str()

        if not (set(passed_args) <= set(self.valid_args)):
            raise IllegalArgumentError(
                f'Illegal argument is passed to the decorator, '
                f'allowed arguments are {self.valid_args}'
            )

    def _validate_multiple_fields(self):
        """
        Check if fields argument is passed, other arguments are not passed,
        otherwise return IllegalArgumentError.
        """
        if self.fields and not (self.field is None and self.prev is None and self.new is None):
            raise IllegalArgumentError(
                'When field is passed as an argument, '
                'the fields prev and new should be None.'
            )

    def _validate_one_field(self):
        """
        Check if field argument is passed, 'fields' argument is not passed,
        or if 'field' is not passed, the 'prev' and 'new' arguments are not passed also,
        otherwise return IllegalArgumentError.
        """
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
        """
        Validate the compatibility of the passed arguments to the decorator.
        """
        self._validate_valid_args()
        self._validate_multiple_fields()
        self._validate_one_field()


class InnerEventDecoratorFactory:
    """
    This class is a decorator function factory which is compatible with the python's
    @ decorator syntax.
    As an example InnerEventFactory(field='Foo', prev='Bar') will return an InnerEventDecorator
    instance which will be used as actual decorator and will set the 'field' and 'perv' instance
    variables to 'Foo' and 'Bar'.

    For subclassing the 'event_type' should be a unique string and the 'valid_args' should be an
    iterable object to restrict the passed arguments to the decorator or a '*' to accept anything.
    """

    event_type = None
    valid_args = '*'

    def __init__(self, *args, **kwargs):
        """
        Save the passed arguments to the decorator in args and kwargs
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, func):
        """
        Instantiates and returns a new InnerEventDecorator.

        :param func: the decorated function (The handler or action function)
        :return: InnerEventDecorator instance
        """
        cls = self.__class__
        return InnerEventDecorator(func, cls.event_type, cls.valid_args, *self.args, **self.kwargs)


class PreCreateEvent(InnerEventDecoratorFactory):
    """
    Called right before the save() method of an instance when is created.
    """
    event_type = constants.PRE_CREATE
    valid_args = ['field', 'new']


class PostCreateEvent(InnerEventDecoratorFactory):
    """
    Called right after the save() method of an instance when is created.
    """
    event_type = constants.POST_CREATE
    valid_args = ['field', 'new']


class PreSaveEvent(InnerEventDecoratorFactory):
    """
    Called right before the save() method of an instance when is saved. This event won't called
    when a new object is created.
    """
    event_type = constants.PRE_SAVE
    valid_args = '*'


class PostSaveEvent(InnerEventDecoratorFactory):
    """
    Called right after the save() method of an instance when is saved. This event won't called
    when a new object is created.
    """
    event_type = constants.POST_SAVE
    valid_args = '*'


class PreDeleteEvent(InnerEventDecoratorFactory):
    """
    Called right before the delete() method of an instance when it is deleted.
    """
    event_type = constants.PRE_DELETE
    valid_args = []


class PostDeleteEvent(InnerEventDecoratorFactory):
    """
    Called right after the delete() method of an instance when it is deleted.
    """
    event_type = constants.POST_DELETE
    valid_args = []


class FKChangeEvent(InnerEventDecoratorFactory):
    """
    Called when fields of the pointing foreign object is changed.
    """
    event_type = constants.FK_CHANGE
    valid_args = ['field']


class M2MChangeEvent(InnerEventDecoratorFactory):
    event_type = constants.M2M_CHANGE
    valid_args = ['field']
