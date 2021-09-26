import inspect

from django.db import models

from model_events.decorators import PreSaveEvent, PreCreateEvent, PostCreateEvent, PostSaveEvent, PreDeleteEvent, \
    PostDeleteEvent, FKChangeEvent
from model_events.models import EventActionModel


def mockable_function(_):
    return _


class TFKModel(EventDrivenModel):
    char_field = models.CharField(max_length=1024)


class TFKModel2(EventDrivenModel):
    char_field = models.CharField(max_length=1024)


class TM2MModel(EventDrivenModel):
    char_field = models.CharField(max_length=1024)


class TModel(EventActionModel):
    char_field = models.CharField(max_length=1024)
    fk_field = models.ForeignKey(TFKModel, on_delete=models.SET_NULL, null=True, blank=True)
    fk_field_2 = models.ForeignKey(TFKModel2, on_delete=models.SET_NULL, null=True, blank=True)
    m2m_field = models.ManyToManyField(TM2MModel, null=True)
    int_field = models.IntegerField(default=0)
    boolean_field = models.BooleanField(default=False)
    pre_create_field = models.BooleanField(default=False)
    post_create_field = models.BooleanField(default=False)
    pre_save_field = models.BooleanField(default=False)
    post_save_field = models.BooleanField(default=False)
    pre_delete_field = models.BooleanField(default=False)
    post_delete_field = models.BooleanField(default=False)

    def normal_function(self):
        return mockable_function('normal_function')

    @PreSaveEvent()
    def pre_save_without_args(self):
        mockable_function('pre_save_without_args')
        return None

    @PreSaveEvent(fields=['char_field', 'int_field'])
    def pre_save_multiple_fields(self):
        return mockable_function('pre_save_multiple_fields')

    @PreSaveEvent(field='char_field')
    def pre_save_only_one_field(self):
        return mockable_function('pre_save_only_one_field')

    @PreSaveEvent(field='char_field', prev='Foo1')
    def pre_save_one_field_with_only_prev_value(self):
        return mockable_function(inspect.stack()[0][3])

    @PreSaveEvent(field='char_field', new='Foo2')
    def pre_save_one_field_with_only_new_value(self):
        return mockable_function(inspect.stack()[0][3])

    @PreSaveEvent(field='char_field', prev='Foo1', new='Foo2')
    def pre_save_one_field_with_new_and_prev_values(self):
        return mockable_function('pre_save_one_field_with_new_and_prev_values')

    @PreSaveEvent(field='fk_field')
    def pre_save_foreign_key_change(self):
        return mockable_function('pre_save_foreign_key_change')

    def m2m_change(self):
        raise Exception("Akbar Error!")

    @PreCreateEvent()
    def test_pre_create(self):
        self.pre_create_field = True

    @PostCreateEvent()
    def test_post_create(self):
        self.post_create_field = True

    @PreSaveEvent()
    def test_pre_save(self):
        self.pre_save_field = True

    @PostSaveEvent()
    def test_post_save(self):
        self.post_save_field = True

    @PreDeleteEvent()
    def test_pre_delete(self):
        pass

    @PostDeleteEvent()
    def test_post_delete(self):
        pass

    @FKChangeEvent()
    def test_fk_instance_change(self):
        return mockable_function('test_fk_instance_change')

    @FKChangeEvent(field='fk_field')
    def test_fk_instance_change_defined_field(self):
        return mockable_function('test_fk_instance_change_defined_field')
