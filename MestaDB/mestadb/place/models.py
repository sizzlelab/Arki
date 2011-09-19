# -*- coding: utf-8 -*-
"""
Place - app to save point or polygon-like geometries into the database.

Place model is used to save single-point objects (e.g. exact places).
Area model is used to save single-polygon objects (e.g. parks, neighbourhoods etc).

PostGIS data type 'geography' is used instead of traditional geometry. For further details, see:
http://postgis.refractions.net/documentation/manual-1.5/ch04.html#PostGIS_GeographyVSGeometry
"""

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.auth.models import User

class Realm(models.Model):
    user = models.ForeignKey(User, db_index=True, blank=True, null=True, editable=True)
    public = models.BooleanField(default=False)
    name = models.CharField(max_length=50, editable=True)
    description = models.TextField(blank=True, null=True, editable=True)
    added = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return u"%s" % (self.name)

    class Meta:
        pass


class BaseGeometry(models.Model):
    """Common fields for all Place app's models."""
    user = models.ForeignKey(User, blank=True, null=True)
    realm = models.ForeignKey(Realm)
    name = models.CharField(max_length=150, editable=True)
    description = models.TextField(blank=True, null=True, editable=True)
    added = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    objects = models.GeoManager()

    def __unicode__(self):
        return u"%s (%s)" % (self.name, str(self.geography)[:50])

    class Meta:
        abstract = True


class Spot(BaseGeometry):
    geography = models.PointField(geography=True, editable=True)


class Area(BaseGeometry):
    geography = models.PolygonField(geography=True, editable=True)
    area = models.FloatField(editable=False)

    def save(self, *args, **kwargs):
        """Uses custom SQL to save polygon's area (in square meters) too."""
        from django.db import connection, transaction
        cursor = connection.cursor()
        if self.area is None:
            self.area = 0 # Temporary value
        # CHECKME: is there during next 3 lines wrong area value in the record? Or isolates the transaction this problem?
        super(Area, self).save(*args, **kwargs) # Call the "real" save() method.
        cursor.execute("UPDATE place_area SET area = ST_Area(geography) WHERE id = %s", [self.id])
        transaction.commit_unless_managed()
        # Update object's area too
        cursor.execute("SELECT area FROM place_area WHERE id = %s", [self.id])
        row = cursor.fetchone()
        self.area = row[0]
