# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.db import models
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor
from django_redis.cache import RedisCache as OriginalRedisCache

from .lua import (LUA_CACHE_OBJECT, LUA_COLLECT_GARBAGE, LUA_INVALIDATE_DEPENDENTS)
from .utils import get_fkeys

logger = logging.getLogger('clever_cache')


DEFAULT_TIMEOUT = getattr(settings, 'CLEVER_CACHE_DEFAULT_TIMEOUT', 24 * 60 * 60)


def is_related_manager(obj):
    if (hasattr(obj, 'field') and hasattr(obj, 'instance') and
            hasattr(obj.field, 'rel') and hasattr(obj.field.rel, 'get_accessor_name')):
        related_name = obj.field.rel.get_accessor_name()
        model = obj.instance.__class__
        if isinstance(getattr(model, related_name, None), ReverseManyToOneDescriptor):
            return True
    else:
        return False


class RedisCache(OriginalRedisCache):
    @property
    def client(self):
        """
        Lazy client connection property.
        """
        if self._client is None:
            self._client = self._client_cls(self._server, self._params, self)

            # registring lua scripts:
            redis = self._client.get_client()
            self._client.cache_object = redis.register_script(LUA_CACHE_OBJECT)
            self._client.invalidate_dependents = redis.register_script(LUA_INVALIDATE_DEPENDENTS)
            self._client.collect_garbage = redis.register_script(LUA_COLLECT_GARBAGE)
        return self._client

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, depends_on=None):
        """
            saves object to cache and links it with dependencies
        """
        keys = []
        argv = []

        cache_key = self.client.make_key(key)
        keys.append(cache_key)

        argv.append(self.client.encode(value))
        if timeout:
            argv.append(timeout)

        depends_on = depends_on or []
        depends_on_keys = []
        for dependency in depends_on:
            depends_on_keys.append(self.make_dependency_key(dependency))

        keys.extend(depends_on_keys)

        logger.debug(
            "cache_set key={0!r} value={1!r} depends_on={2!r}".format(
                cache_key, value, depends_on_keys
            )
        )
        self.client.cache_object(keys=keys, args=argv)

    def make_dependency_key(self, obj):
        """
            if obj is model class:
                clever_cache_deps:appname_modelname
            if obj is model instance:
                clever_cache_deps:appname_modelname_pk
        """
        if isinstance(obj, type) and issubclass(obj, models.Model):
            str_key = "clever_cache_deps:{model_name}".format(
                model_name=obj._meta.db_table
            )

        elif isinstance(obj, models.Model):
            str_key = "clever_cache_deps:{model_name}_{pk}".format(
                model_name=obj._meta.db_table,
                pk=obj.pk
            )
        elif is_related_manager(obj):
            str_key = "clever_cache_deps:{model_name}_{pk}_{related_name}".format(
                model_name=obj.instance._meta.db_table,
                pk=obj.instance.pk,
                related_name=obj.field.rel.get_accessor_name()
            )
        else:
            raise TypeError("instance of {!r} cannot be used as dependency".format(
                type(obj)
            ))

        return self.make_key(str_key)

    def invalidate_dependents(self, *objects):
        """
            deletes from cache items that depends on obj
        """
        dependents_keys = []

        for obj in objects:
            if isinstance(obj, type) and issubclass(obj, models.Model):
                dependents_keys.append(self.make_dependency_key(obj))
            elif isinstance(obj, models.Model):
                dependents_keys.append(self.make_dependency_key(obj))
                dependents_keys.append(self.make_dependency_key(obj.__class__))
                dependents_keys.extend(self.make_ancestors_related_fields_dependency_keys(obj))

        deleted_keys = self.client.invalidate_dependents(keys=dependents_keys)

        logger.debug(
            "cache_invalidation dependents_keys={0!r}, deleted_keys={1!r}".format(
                dependents_keys, deleted_keys
            )
        )

    def make_ancestors_related_fields_dependency_keys(self, instance):
        keys = []
        initial_fks_values = getattr(instance, '_initial_fks_values', {})
        for fk in get_fkeys(instance):
            initial_parent_id = initial_fks_values.get(fk.attname)
            parent_id = getattr(instance, fk.attname)
            perent_model = fk.rel.model
            parent_related_name = fk.rel.get_accessor_name()
            key_template = "clever_cache_deps:{model_name}_{pk}_{related_name}"
            str_key = key_template.format(
                model_name=perent_model._meta.db_table,
                pk=parent_id,
                related_name=parent_related_name
            )
            key = self.make_key(str_key)
            keys.append(key)
            if initial_parent_id and initial_parent_id != parent_id:
                str_key = key_template.format(
                    model_name=perent_model._meta.db_table,
                    pk=initial_parent_id,
                    related_name=parent_related_name
                )
                key = self.make_key(str_key)
                keys.append(key)
        return keys
