# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.fields.related import ForeignKey


def get_fkeys(instance):
    return (field for field in instance._meta.fields if isinstance(field, ForeignKey))
