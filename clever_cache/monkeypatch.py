# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.cache import cache
from django.db.models import QuerySet
from django.db.models.signals import (m2m_changed, post_delete, post_init, post_save)

from .utils import get_fkeys

old_post_init_send = post_init.send


def new_post_init_send(instance, *args, **kwargs):
    initial_fks_values = {}
    for fk in get_fkeys(instance):
        initial_fks_values[fk.attname] = getattr(instance, fk.attname)
    instance._initial_fks_values = initial_fks_values
    signal_result = old_post_init_send(instance=instance, *args, **kwargs)
    return signal_result


post_init.send = new_post_init_send


def patch_signal(signal):
    old_send = getattr(signal, 'send')

    def new_send(instance, *args, **kwargs):
        result = old_send(instance=instance, *args, **kwargs)
        cache.invalidate_dependents(instance)
        return result

    new_send.__name__ = old_send.__name__
    new_send.__dict__.update(old_send.__dict__)
    setattr(signal, 'send', new_send)


patch_signal(post_delete)
patch_signal(post_save)


old_m2m_changed_send = m2m_changed.send


def new_m2m_changed_send(instance, action, model, pk_set, *args, **kwargs):
    affected_objects = [instance]
    result = old_m2m_changed_send(
        instance=instance, action=action, model=model, pk_set=pk_set,
        *args, **kwargs
    )

    if action in ('post_add', 'post_remove', 'post_clear'):
        if action in ('post_add', 'post_remove'):
            for pk in pk_set:
                affected_objects.append(model(pk=pk))
        else:
            affected_objects.append(model)
        cache.invalidate_dependents(*affected_objects)

    return result


new_m2m_changed_send.__name__ = old_m2m_changed_send.__name__
new_m2m_changed_send.__dict__.update(old_m2m_changed_send.__dict__)
m2m_changed.send = new_m2m_changed_send


def patch_qs_method(method_name):
    old_method = getattr(QuerySet, method_name)

    def new_method(self, *args, **kwargs):
        result = old_method(self, *args, **kwargs)
        cache.invalidate_dependents(self.model)
        return result
    new_method.__name__ = old_method.__name__
    new_method.__dict__.update(old_method.__dict__)
    setattr(QuerySet, method_name, new_method)


patch_qs_method('delete')
patch_qs_method('update')
patch_qs_method('bulk_create')
