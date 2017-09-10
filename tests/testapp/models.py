# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class User(models.Model):
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return self.name


class Post(models.Model):
    author = models.ForeignKey(User)
    title = models.CharField(max_length=32)
    body = models.CharField(max_length=64)
    tags = models.ManyToManyField(Tag)

    def __unicode__(self):
        return self.title


class Comment(models.Model):
    author = models.ForeignKey(User)
    post = models.ForeignKey(Post)
    body = models.CharField(max_length=64)

    def __unicode__(self):
        return self.body
