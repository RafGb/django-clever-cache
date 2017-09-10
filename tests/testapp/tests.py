# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time

from django.core.cache import cache
from django.test import TestCase

from .models import Comment, Post, Tag, User


class CacheTestMixin(object):
    def assertInCache(self, cache_key):
        self.assertTrue(cache.get(cache_key))

    def assertNotInCache(self, cache_key):
        self.assertIsNone(cache.get(cache_key))


class InvalidationTest(CacheTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(InvalidationTest, cls).setUpClass()
        redis = cache.client.get_client()
        redis.flushdb()

        cls.user = User.objects.create(name='raf')

        cls.music_tag = Tag.objects.create(name='music')
        cls.dev_tag = Tag.objects.create(name='dev')
        cls.life_tag = Tag.objects.create(name='life')

        cls.first_post = Post.objects.create(
            author=cls.user,
            title='привет!',
            body='Hello world!'
        )
        cls.first_post.tags.add(cls.dev_tag)

        cls.second_post = Post.objects.create(
            author=cls.user,
            title='hi again!',
            body='check out my mixtape'
        )
        cls.second_post.tags.add(cls.music_tag)

        cache.set('dont_invalidate_this_key', cls.first_post, depends_on=[])

    def tearDown(self):
        self.assertInCache('dont_invalidate_this_key')

    def test_object_change_invalidation(self):
        cache_key = 'first_post_key'
        self.assertNotInCache(cache_key)
        # test object field change
        cache.set(cache_key, self.first_post, depends_on=[self.first_post])
        self.assertInCache(cache_key)
        self.first_post.title = 'hi there!'
        self.first_post.save()
        self.assertNotInCache(cache_key)
        # test m2m field change
        cache.set(cache_key, self.first_post, depends_on=[self.first_post])
        self.assertInCache(cache_key)
        new_tag = Tag.objects.create(name='debugging')
        self.first_post.tags.add(new_tag)
        self.assertNotInCache(cache_key)

    def test_m2m_change_invalidation(self):
        cache_key = 'dev_tag'

        # remove
        cache.set(cache_key, self.dev_tag, depends_on=[self.dev_tag])
        self.assertInCache(cache_key)
        self.first_post.tags.remove(self.dev_tag)
        self.assertNotInCache(cache_key)

        # clear
        cache.set(cache_key, self.dev_tag, depends_on=[Tag])
        self.assertInCache(cache_key)
        self.first_post.tags.clear()
        self.assertNotInCache(cache_key)

        # add
        cache.set(cache_key, self.dev_tag, depends_on=[self.dev_tag])
        self.assertInCache(cache_key)
        self.first_post.tags.add(self.dev_tag)
        self.assertNotInCache(cache_key)

    def test_model_change_invalidation(self):
        cache_key = 'posts_all'
        posts = Post.objects.all().select_related('author')
        # another object save
        cache.set(cache_key, posts, depends_on=[Post, User])
        self.assertInCache(cache_key)
        new_post = Post.objects.create(
            author=self.user,
            title='third',
            body='sup.'
        )
        self.assertNotInCache(cache_key)
        # update
        cache.set(cache_key, posts, depends_on=[Post, User])
        self.assertInCache(cache_key)
        User.objects.update(name='rafis')
        self.assertNotInCache(cache_key)
        # delete
        cache.set(cache_key, posts, depends_on=[Post, User])
        self.assertInCache(cache_key)
        new_post.delete()
        self.assertNotInCache(cache_key)
        # bulk_create
        cache.set(cache_key, posts, depends_on=[Post, User])
        self.assertInCache(cache_key)
        User.objects.bulk_create([
            User(name='foo_1'),
            User(name='foo_2')
        ])
        self.assertNotInCache(cache_key)
        # queryset delete
        cache.set(cache_key, posts, depends_on=[Post, User])
        self.assertInCache(cache_key)
        User.objects.filter(name__startswith='foo').delete()
        self.assertNotInCache(cache_key)

    def test_realted_manager_invalidation(self):
        cache_key = 'second_post_key'
        self.assertNotInCache(cache_key)
        # create child
        cache.set(
            cache_key, self.second_post,
            depends_on=[self.second_post, self.second_post.comment_set]
        )
        self.assertInCache(cache_key)
        comment = Comment.objects.create(
            author=self.user, post=self.second_post, body='first comment!'
        )
        self.assertNotInCache(cache_key)

        # change child's fk
        cache.set(
            cache_key, self.second_post,
            depends_on=[self.second_post, self.second_post.comment_set]
        )
        self.assertInCache(cache_key)
        comment.post = self.first_post
        comment.save()
        self.assertNotInCache(cache_key)

        cache.set(
            cache_key, self.second_post,
            depends_on=[self.second_post, self.second_post.comment_set]
        )
        self.assertInCache(cache_key)
        comment.post = self.second_post
        comment.save()
        self.assertNotInCache(cache_key)

        # delete child
        cache.set(
            cache_key, self.second_post,
            depends_on=[self.second_post, self.second_post.comment_set]
        )
        self.assertInCache(cache_key)
        comment.delete()
        self.assertNotInCache(cache_key)

    def test_incorrect_dependency(self):
        with self.assertRaises(TypeError):
            cache.set(key='foo', value='bar', depends_on=['biz'])


class TimeoutTest(CacheTestMixin, TestCase):
    def setUp(self):
        redis = cache.client.get_client()
        redis.flushdb()
        self.some_tag = Tag.objects.create(name='whatever')

    def test_timeout(self):
        cache.set(key='foo', value='bar', depends_on=[self.some_tag], timeout=1)
        time.sleep(1)

        # item should be deleted
        self.assertNotInCache('foo')
        # dependency should be deleted too
        self.assertNotInCache(cache.make_dependency_key(self.some_tag))
