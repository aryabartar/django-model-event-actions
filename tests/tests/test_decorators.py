from unittest import mock

from event_actions import constants
from event_actions.decorators import PreSaveEvent, InnerEventDecoratorFactory
from event_actions.exceptions import IllegalArgumentError
from tests.exception import DeleteTestException
from tests.models import TModel, TFKModel, TFKModel2
from tests.tests.base import TestBase


class TestEventDecorator(TestBase):
    def setUp(self):
        self.instance = TModel.objects.create(
            char_field='Foo',
            int_field=1
        )

    def test_decorator_function_arguments(self):
        method_instance = self.instance.pre_save_one_field_with_new_and_prev_values

        self.assertEqual(method_instance.field, 'char_field')
        self.assertEqual(method_instance.prev, 'Foo1')
        self.assertEqual(method_instance.new, 'Foo2')

    def test_validate_arguments(self):
        PreSaveEvent()(TModel.normal_function)
        PreSaveEvent(field='Foo')(TModel.normal_function)
        PreSaveEvent(field='Foo', prev='Bar')(TModel.normal_function)
        PreSaveEvent(field='Foo', new='Bar')(TModel.normal_function)
        PreSaveEvent(field='Foo', prev='Bar', new='Bar')(TModel.normal_function)
        PreSaveEvent(fields=['Foo1', 'Foo2'])(TModel.normal_function)

    def test_validate_arguments_raises_illegal_argument_error(self):
        class TestDecorator(InnerEventDecoratorFactory):
            event_type = constants.PRE_SAVE
            valid_args = ['field']

        with self.assertRaises(IllegalArgumentError):
            PreSaveEvent(prev='Bar')(TModel.normal_function)
        with self.assertRaises(IllegalArgumentError):
            PreSaveEvent(field='Foo', fields=['Foo1', 'Foo2'])(TModel.normal_function)
        with self.assertRaises(IllegalArgumentError):
            PreSaveEvent(fields=['Foo1', 'Foo2'], prev='Bar')(TModel.normal_function)
        TestDecorator(field='Foo')(TModel.normal_function)
        with self.assertRaises(IllegalArgumentError):
            TestDecorator(fields=['Foo'])(TModel.normal_function)

    def test_actions_trigger_without_args(self):
        instance = self.instance

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'New Foo'
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_without_args')

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.delete()
            self.assert_not_calls(mocked_function, 'pre_save_without_args')

        with mock.patch('tests.models.mockable_function') as mocked_function:
            TModel.objects.create(
                char_field='Foo',
                int_field=1
            )
            self.assertFalse(mocked_function.called)

    def test_actions_trigger_multiple_fields_arg(self):
        instance = self.instance

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'New Foo'
            instance.int_field = -1
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_multiple_fields')

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'New New Foo'
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_multiple_fields')

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.boolean_field = not instance.boolean_field
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_multiple_fields')

    def test_actions_trigger_with_field_arg(self):
        instance = self.instance

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'New Foo'
            instance.int_field = -1
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_only_one_field')

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'New New Foo'
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_only_one_field')

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.boolean_field = not instance.boolean_field
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_only_one_field')

    def test_actions_trigger_with_field_and_prev_arg(self):
        instance = self.instance
        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'New Foo'
            instance.int_field = -1
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_one_field_with_only_prev_value')

        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'New Foo'
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_one_field_with_only_prev_value')

        instance.char_field = 'Foo2'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'Foo1'
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_one_field_with_only_prev_value')

        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.boolean_field = not instance.boolean_field
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_one_field_with_only_prev_value')

    def test_actions_trigger_with_field_and_new_arg(self):
        instance = self.instance
        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'Foo2'
            instance.int_field = -1
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_one_field_with_only_new_value')

        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'Foo2'
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_one_field_with_only_new_value')

        instance.char_field = 'Foo2'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'Foo1'
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_one_field_with_only_new_value')

        instance.char_field = 'Foo2'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.boolean_field = not instance.boolean_field
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_one_field_with_only_new_value')

    def test_two_actions_trigger_for_prev_and_new_field_arg(self):
        instance = self.instance
        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'Foo2'
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_one_field_with_only_prev_value')
            self.assert_calls(mocked_function, 'pre_save_one_field_with_only_new_value')

    def test_actions_trigger_with_field_and_new_and_prev_arg(self):
        instance = self.instance
        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'Foo2'
            instance.int_field = -1
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_one_field_with_new_and_prev_values')

        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'Foo2'
            instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_one_field_with_new_and_prev_values')

        instance.char_field = 'Foo2'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.char_field = 'Foo1'
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_one_field_with_new_and_prev_values')

        instance.char_field = 'Foo1'
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            instance.boolean_field = not instance.boolean_field
            instance.save()
            self.assert_not_calls(mocked_function, 'pre_save_one_field_with_new_and_prev_values')

    def test_action_triggers_on_fk(self):
        instance = self.instance
        fk_1 = TFKModel.objects.create(char_field='Foo')

        instance.fk_field = fk_1
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            fk_2 = TFKModel.objects.create(char_field='Foo')
            instance.fk_field = fk_2
            instance.save()

            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'pre_save_foreign_key_change')

    def test_pre_create_decorator(self):
        instance = self.instance
        self.assertTrue(instance.pre_create_field)

        instance.pre_create_field = False
        instance.save()
        instance.refresh_from_db()
        self.assertFalse(instance.pre_create_field)

    def test_post_create_decorator(self):
        instance = self.instance
        self.assertTrue(instance.post_create_field)
        instance.refresh_from_db()
        self.assertFalse(instance.post_create_field)

        instance.post_create_field = False
        instance.save()
        instance.refresh_from_db()
        self.assertFalse(instance.post_create_field)

    def test_pre_save_decorator(self):
        instance = self.instance
        self.assertFalse(instance.pre_save_field)
        instance.refresh_from_db()
        self.assertFalse(instance.pre_save_field)

        instance.save()
        self.assertTrue(instance.pre_save_field)
        instance.refresh_from_db()
        self.assertTrue(instance.pre_save_field)

    def test_post_save_decorator(self):
        instance = self.instance
        self.assertFalse(instance.post_save_field)
        instance.refresh_from_db()
        self.assertFalse(instance.post_save_field)

        instance.save()
        self.assertTrue(instance.post_save_field)
        instance.refresh_from_db()
        self.assertFalse(instance.post_save_field)

    def test_pre_delete_decorator(self):
        instance = self.instance

        with mock.patch('tests.tests.test_decorators.TModel.test_pre_delete', autospec=True) as mocked_func:
            mocked_func.side_effect = DeleteTestException()
            with self.assertRaises(DeleteTestException):
                instance.delete()

        instance.refresh_from_db()
        self.assertIsNotNone(instance.id)

        instance.delete()
        with self.assertRaises(TModel.DoesNotExist):
            instance.refresh_from_db()

    def test_post_delete_decorator(self):
        instance = self.instance

        with mock.patch('tests.tests.test_decorators.TModel.test_post_delete', autospec=True) as mocked_func:
            mocked_func.side_effect = DeleteTestException()
            with self.assertRaises(DeleteTestException):
                instance.delete()

        with self.assertRaises(TModel.DoesNotExist):
            instance.refresh_from_db()

    def test_fk_change(self):
        instance = self.instance
        fk_instance = TFKModel.objects.create(char_field='Foo!')
        fk_instance_2 = TFKModel2.objects.create(char_field='Foo!')

        instance.fk_field = fk_instance
        instance.fk_field_2 = fk_instance_2
        instance.save()

        with mock.patch('tests.models.mockable_function') as mocked_function:
            fk_instance.char_field = 'New Foo'
            fk_instance.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'test_fk_instance_change')
            self.assert_calls(mocked_function, 'test_fk_instance_change_defined_field')

        with mock.patch('tests.models.mockable_function') as mocked_function:
            fk_instance_2.char_field = 'Other New Foo'
            fk_instance_2.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'test_fk_instance_change')
            self.assert_not_calls(mocked_function, 'test_fk_instance_change_defined_field')

        with mock.patch('tests.models.mockable_function') as mocked_function:
            fk_instance_2.char_field = 'Other New Foo'
            fk_instance_2.save()
            self.assertTrue(mocked_function.called)
            self.assert_calls(mocked_function, 'test_fk_instance_change')
            self.assert_not_calls(mocked_function, 'test_fk_instance_change_defined_field')
