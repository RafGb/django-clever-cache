# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class CleverCacheConfig(AppConfig):
    name = 'clever_cache'

    def ready(self):
        import clever_cache.monkeypatch
