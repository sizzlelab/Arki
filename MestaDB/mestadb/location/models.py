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

def get_guid(length=12):
    """
    Generate and return a random string which can be considered unique.
    Default length is 12 characters from set [a-zA-Z0-9].
    """
    alphanum = string.letters + string.digits
    return ''.join([alphanum[random.randint(0,len(alphanum)-1)] for i in xrange(length)])

class Entity(models.Model):
    """
    Entity is an object with geographical coordinates.
    Fields:
    * guid, globally unique id, usually a random string
    * user, foreign key to an Auth.User object
    * name, optional
    * description, optional
    * created and updated, auto-timestamps
    * geography, GIS field for location (see PostGIS 1.5) or
      http://workshops.opengeo.org/postgis-intro/geography.html
    """
    guid = models.CharField(max_length=40, default=get_guid, unique=True, db_index=True)
    user = models.ForeignKey(User, blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, default='', editable=True)
    description = models.TextField(blank=True, default='', editable=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    objects = models.GeoManager()
    geography = models.PointField(geography=True, editable=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, str(self.geography)[:50])
