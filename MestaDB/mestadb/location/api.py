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

# Django 1.3 CSRF stuff
from django.views.decorators.csrf import csrf_exempt

from django.contrib.gis.geos import Point

from django.http import HttpResponse


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
        "uid": unicode(obj.uid),
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

def _nearby_spots_find(point, max_spots=50, max_dist=10000):
    """
    Loop until at least max_spots Spots are found.
    """
    t1 = time.time()
    START = 10 # start from START meters
    CURR_DIST = START
    FACTOR = 1.5 # how much to increase
    res_cnt = 0 # amount of found spots
    loops = 0
    # Loop until max_spots is reached
    while res_cnt < max_spots:
        loops += 1
        # GeoDjango spatial query
        res_cnt = Entity.objects.filter(geography__dwithin=(point, CURR_DIST)).count()
        #print u'%8.1f m: found %d Spots' % (CURR_DIST, res_cnt)
        if CURR_DIST > max_dist: break # Stop after max_dist is reached
        if res_cnt < max_spots: #
            CURR_DIST = CURR_DIST * FACTOR
    t2 = time.time()
    near_spots = Entity.objects.filter(geography__dwithin=(point, CURR_DIST)).distance(point).order_by('distance')[:max_spots]
    t3 = time.time()
    logger.debug(u"Found %s spots in %d loops in %.3f ms" % (res_cnt, loops, (t3-t1)))
    #print t3-t1
    return near_spots

def _entity_nearby_get(point, limit, range):
    near_spots = _nearby_spots_find(point, max_spots=limit, max_dist=range)
    #print u'%8.1f m: found %d Spots' % (CURR_DIST, res_cnt)
    features = []
    for p in near_spots:
        features.append(make_feature(p, p.geography, {'name': p.name or u'%s %.5f %.5f' % (p.uid, p.geography.coords[1], p.geography.coords[0])}))
    data = { 'geojson': make_featurecollection(features) }
    return data

def entity_get(request):
    try:
        lat = float(request.POST.get('lat'))
        lon = float(request.POST.get('lon'))
        point = Point(lon, lat)
        DEFAULT_RANGE = 1000
        DEFAULT_LIMIT = 50
        range = int(request.POST.get('range', DEFAULT_RANGE))
        limit = int(request.POST.get('limit', DEFAULT_LIMIT))
    except TypeError:
        data, message = {}, u'No "lat" or "lon" parameters found.'
        return False, data, message
    data = _entity_nearby_get(point, limit, range)
    message = u'Found %d entities' % len(data['geojson']['features'])
    return True, data, message

def entity_post(request):
    data = request.POST.get('json', {})
    if not data: # json did not exist
        data['name'] = request.POST.get('name')
        try:
            lat = float(request.POST.get('lat'))
            lon = float(request.POST.get('lon'))
            point = Point(lon, lat)
        except TypeError:
            data, message = {}, u'No "lat" or "lon" parameters found.'
            return False, data, message
    e = Entity(geography=point)
    e.save()
    data, message = {'uid': e.uid}, u'201 Created'
    return True, data, message

POST_CALLS = {
    'entity_post': entity_post,
    'entity_get': entity_get,
}
