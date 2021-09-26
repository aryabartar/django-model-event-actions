from django.test import TestCase


class TestBase(TestCase):
    def assert_calls(self, mocked_function, call_value):
        mocked_function.assert_any_call(call_value)

    def assert_not_calls(self, *args, **kwargs):
        with self.assertRaises(AssertionError):
            self.assert_calls(*args, **kwargs)
