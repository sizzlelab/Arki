# -*- coding: utf-8 -*-
"""
Location - app to save location aware objects into the database.
This is created for ASI (Aalto Social Interface).

PostGIS data type 'geography' is used instead of traditional geometry. For further details, see:
http://postgis.refractions.net/documentation/manual-1.5/ch04.html#PostGIS_GeographyVSGeometry
"""

import string
import random

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.auth.models import User

def get_uid(length=12):
    """
    Generate and return a random string which can be considered unique.
    Default length is 12 characters from set [a-zA-Z0-9].
    """
    alphanum = string.letters + string.digits
    return ''.join([alphanum[random.randint(0,len(alphanum)-1)] for i in xrange(length)])


#class Realm(models.Model):
#    user = models.ForeignKey(User, db_index=True, blank=True, null=True, editable=True)
#    public = models.BooleanField(default=False)
#    name = models.CharField(max_length=50, editable=True)
#    description = models.TextField(blank=True, null=True, editable=True)
#    added = models.DateTimeField(auto_now_add=True, editable=False)
#    updated = models.DateTimeField(auto_now=True, editable=False)
#
#    def __unicode__(self):
#        return u"%s" % (self.name)
#
#    class Meta:
#        pass


class Entity(models.Model):
    """Common fields for all Place app's models."""
    uid = models.CharField(max_length=40, unique=True, db_index=True, default=get_uid, editable=False)
    user = models.ForeignKey(User, blank=True, null=True)
#    realm = models.ForeignKey(Realm)
    name = models.CharField(max_length=150, editable=True)
    description = models.TextField(blank=True, editable=True)
    added = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    objects = models.GeoManager()
    geography = models.PointField(geography=True, editable=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, str(self.geography)[:50])

