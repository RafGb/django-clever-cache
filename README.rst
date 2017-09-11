django-clever-cache
===================

Django cache backend with automatic granular invalidation.

Requires
--------

-  django >= 1.8
-  redis >= 3.0
-  django-redis

Installation and setup
----------------------

.. code:: sh

    $ pip install django-clever-cache

in settings.py: add ``clever_cache`` to INSTALLED\_APPS, and set
``clever_cache.backend.RedisCache`` as your cache backend.

.. code:: python

    CACHES = {
        "default": {
            "BACKEND": 'clever_cache.backend.RedisCache',
            "LOCATION": "redis://127.0.0.1:6379/1",
            "OPTIONS": {
                'DB': 1,
            }
        }
    }

Usage
-----

to save value in cache use standart function
``django.core.cache.cache.set`` with optional argument ``depends_on``:
``cache.set(key, value, depends_on=[<dependencies_list>])``

Dependency can be:

Model class
~~~~~~~~~~~
if you set model class as dependency (``cache.set(key, value, depends_on=[SomeModel])``), and change any
instance of SomeModel, call ``bulk_create``, ``update`` or ``delete`` to
model's queryset, key will be invalidated.

Model instance
~~~~~~~~~~~~~~

if you set model instance as dependency
(``cache.set(key, value, depends_on=[some_instance])``), and change this
instance(including changing m2m fields), key will be invalidated.

Related manger
~~~~~~~~~~~~~~

Let's assume you have following models:

.. code:: python

    class Parent(models.Model):
        name = models.CharField(max_length=32)

    class Child(models.Model):
        parent = models.ForeignKey(Parent)
        name = models.CharField(max_length=32)

    some_parent = Parent.objects.get(id=42)

so, if you set related manager as a dependency
(``cache.set(key, value, depends_on=[some_parent.child_set])``), and
change any Child object with parent = some\_parent, key will be
invalidated.
