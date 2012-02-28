# -*- coding: utf-8 -*-

import os
import re
import time
import hashlib
import mimetypes
import PIL.Image
import string
import random
import datetime
import tempfile

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.gis.geos import *

from content.models import Content

def get_uid(length=12):
    """
    Generate and return a random string which can be considered unique.
    Default length is 12 characters from set [a-zA-Z0-9].
    """
    alphanum = string.letters + string.digits
    return ''.join([alphanum[random.randint(0,len(alphanum)-1)] for i in xrange(length)])


class Authkey(models.Model):
    user = models.ForeignKey(User)
    key = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    used = models.DateTimeField(auto_now=True)


class Tag(models.Model):
    uid = models.CharField(max_length=40, unique=True, db_index=True, default=get_uid, editable=False)
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Egg(models.Model):
    uid = models.CharField(max_length=40, unique=True, db_index=True, default=get_uid, editable=False)
    privacy = models.CharField(max_length=40, default="PRIVATE",
                               choices=(("PRIVATE", "Private"),
                                        ("RESTRICTED", "Restricted"),
                                        ("PUBLIC", "Public")))
    user = models.ForeignKey(User, blank=True, null=True, editable=True)
    tags = models.ManyToManyField(Tag, blank=True, editable=True)
    content = models.ForeignKey(Content, null=True, editable=True)
    title = models.CharField(max_length=200, blank=True)
    caption = models.TextField(blank=True)
    author = models.CharField(max_length=200, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    point = models.PointField(geography=True, blank=True, null=True, editable=True)
    objects = models.GeoManager()

    def latlon(self):
        return self.point.coords if self.point else None

    def __unicode__(self):
        return u'%s: %s' % (self.author, self.caption)


    #def egg2content(self):
    #    if self.content is not None:
    #        self.content.point = self.point
    #        self.content.title = self.title
    #        self.content.caption = self.caption
    #        self.content.author = self.author
    #        self.content.save()
    #
    #def content2egg(self):
    #    if self.content is not None:
    #        self.point = self.content.point
    #        self.title = self.content.title
    #        self.caption = self.content.caption
    #        self.author = self.content.author
    #        self.save()
    #
    #def save(self, *args, **kwargs):
    #    self.egg2content()
    #    super(Egg, self).save(*args, **kwargs) # Call the "real" save() method.

class Comment(models.Model):
    uid = models.CharField(max_length=40, unique=True, db_index=True, default=get_uid, editable=False)
    user = models.ForeignKey(User, null=True, editable=False)
    egg = models.ForeignKey(Egg, null=False, editable=False, related_name='comments')
    title = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=False)
    author = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: %s' % (self.author, self.text)

