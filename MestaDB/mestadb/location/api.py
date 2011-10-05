# -*- coding: utf-8 -*-
"""
API for Location application.

# TODO:
- create entity
- get entity(id)
- search entity(lat, lon, limit, maxrange)
- search entity([id1, id2, id3, ...])

"""

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError
# Django 1.3 CSRF stuff
from django.views.decorators.csrf import csrf_exempt


from models import Entity
import logging
logger = logging.getLogger('django')

import os
import datetime
import time
import json


"""
API functions:
- entity_post
- entity_put
- entity_delete
- entity_get
 - single
 - search

"""

def make_feature(obj, geo, properties = {}):
    """
    Creates GeoJSON Feature from geographically enabled object 'obj'.
    Geometry 'geo' must be passed separately.
    Optional 'properties' dict is placed 'as is' into Feature's properties
    Id is get from obj.id.
    TODO: check how id could be determined automatically or optionally passed as a parameter.
    """
    feature = {
        "type": "Feature",
        "guid": unicode(obj.guid),
        "properties": properties,
        "geometry": json.loads(geo.json)
    }
    if geo.geom_type != 'Point':
        # Create geojson bbox from geography's boundary corner Points
        # TODO: there must be simplier way!
        # [min lon, min lat, max lon, max lat]
        try:
            xlist = [x[0] for x in geo.boundary.coords]
            ylist = [x[1] for x in geo.boundary.coords]
            xlist.sort()
            ylist.sort()
            feature['bbox'] = [xlist[0], ylist[0], xlist[1], ylist[1] ]
        except IndexError: # geo.boundary may be MULTIPOINT EMPTY
            pass
    return feature

def make_featurecollection(features):
    featurecollection = {
      "type": "FeatureCollection",
      #"bbox": [100.0, 0.0, 105.0, 1.0],
       "features": features
    }
    return featurecollection

def _nearby_entities_find(entities, point, limit=50, range=10000):
    """
    Loop until at least limit Spots are found.
    """
    t1 = time.time()
    START = 10 # start from START meters
    CURR_DIST = START
    FACTOR = 1.5 # how much to increase
    res_cnt = 0 # amount of found spots
    loops = 0
    # Loop until limit is reached
    while res_cnt < limit:
        loops += 1
        # GeoDjango spatial query
        res_cnt = entities.filter(geography__dwithin=(point, CURR_DIST)).count()
        #print u'%8.1f m: found %d Spots' % (CURR_DIST, res_cnt)
        if CURR_DIST > range: break # Stop after range is reached
        if res_cnt < limit: #
            CURR_DIST = CURR_DIST * FACTOR
    t2 = time.time()
    near_spots = entities.filter(geography__dwithin=(point, CURR_DIST)).distance(point).order_by('distance')[:limit]
    t3 = time.time()
    logger.debug(u"Found %s Entities in %d loops in %.3f ms" % (res_cnt, loops, (t3-t1)))
    #print t3-t1
    return near_spots

def entity_get(request):
    entities = Entity.objects.all()
    try:
        request_data = json.loads(request.GET.get('data', ''))
    except ValueError:
        request_data = request.GET
    # Set up limits
    DEFAULT_RANGE = 1000
    DEFAULT_LIMIT = 50
    # FIXME: try/except ValueError and return error
    try:
        range = int(request_data.get('range', DEFAULT_RANGE))
        limit = int(request_data.get('limit', DEFAULT_LIMIT))
    except ValueError:
        data, message = {}, u'"range" and "limit" should be numeric.'
        return False, data, message
    # 1. filter by guid_list if it exists:
    if 'guid_list' in request_data:
        guid_list = request_data['guid_list']
        if isinstance(guid_list, basestring):
            guid_list = guid_list.split(',')
        entities = entities.filter(guid__in=guid_list)
    # 2. filter by last_modified_after if it exists
    if 'last_modified_after' in request_data:
        entities = entities.filter(updated__gt=request_data['last_modified_after'])
    # 3. Filter by coordinates and range, if lat & lon exist
    try:
        lat = float(request_data.get('lat'))
        lon = float(request_data.get('lon'))
        point = Point(lon, lat)
    except ValueError:
        data, message = {}, u'"lat" and "lon" should be numeric.'
        return False, data, message
    except TypeError:
        point = None # it is okay there wasn't no lat and lon
    if point:
        try:
            entities = _nearby_entities_find(entities, point, limit, range)
        except DatabaseError, message:
            return False, {}, str(message).strip() + " (lat=%.5f,lon=%.5f)" % (lat, lon)
    else:
        entities = entities.order_by('-updated')[:limit]
    features = []
    for obj in entities:
        features.append(make_feature(obj, obj.geography, {
            'name': obj.name or u'%s %.5f %.5f' % (obj.guid, obj.geography.coords[1], obj.geography.coords[0]),
            'updated': obj.updated.strftime('%Y%m%dT%H%M%S'),
        }))
    data = { 'geojson': make_featurecollection(features) }
    message = u'Found %d entities' % len(data['geojson']['features'])
    return True, data, message

def entity_post(request):
    """
    Create a new Entity with optional predefined GUID.
    If Entity with given GUID already exists, it will be replaced with new data.
    Parameters can be separate parameters in request.POST or
    JSON encoded in a singe "data" parameter.
    Currently successful creation returns always 201 Created.
    """
    try:
        request_data = json.loads(request.POST.get('data', ''))
    except ValueError:
        request_data = {}
    if not request_data: # json data did not exist
        request_data['name'] = request.POST.get('name', '')
        try:
            lat = float(request.POST.get('lat'))
            lon = float(request.POST.get('lon'))
            request_data['geography'] = Point(lon, lat)
        except TypeError:
            data, message = {}, u'No "lat" or "lon" parameters found.'
            return False, data, message
    guid = request.POST.get('guid')
    if guid:
        request_data['guid'] = request.POST.get('guid')
    try: # to get existing Entity from the database
        ent = Entity.objects.get(guid=guid)
        ent.geography = request_data['geography'] # update location
    except Entity.DoesNotExist: # if it fails, create a new one
        ent = Entity(**request_data)
        #try:
        #   ent.validate_unique()
        #except ValidationError, e:
        #    data, message = {}, u'Entity with uid "%s" already exists.' % (ent.uid)
        #    return False, data, message
    ent.save()
    data, message = {'guid': ent.guid}, u'201 Created'
    return True, data, message

POST_CALLS = {
    'entity_post': entity_post,
    'entity_get': entity_get,
}
