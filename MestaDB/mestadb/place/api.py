# -*- coding: utf-8 -*-
"""
API for Track application.
"""

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
#from django.contrib.auth import authenticate, login, logout
#from django.contrib.auth.decorators import login_required

# Django 1.3 CSRF stuff
from django.views.decorators.csrf import csrf_exempt

from django.contrib.gis.geos import Point

#from track.models import Trackpoint
#from track.models import Trackseg

from place.models import Spot

import models
import logging
logger = logging.getLogger('django')

import os
import datetime
import time
import json

"""
TODO:
- realm_get_all():
- realm_get(uid/name)
"""

"""
API functions:

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
        "id": unicode(obj.id),
        "properties": properties,
        #"bbox": [-180.0, -90.0, 180.0, 90.0], # min lon, min lat, max lon, max lat
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
        res_cnt = Spot.objects.filter(geography__dwithin=(point, CURR_DIST)).count()
        #print u'%8.1f m: found %d Spots' % (CURR_DIST, res_cnt)
        if CURR_DIST > max_dist: break # Stop after max_dist is reached
        if res_cnt < max_spots: #
            CURR_DIST = CURR_DIST * FACTOR
    t2 = time.time()
    near_spots = Spot.objects.filter(geography__dwithin=(point, CURR_DIST)).distance(point).order_by('distance')[:max_spots]
    t3 = time.time()
    logger.debug(u"Found %s spots in %d loops in %.3f ms" % (res_cnt, loops, (t3-t1)))
    #print t3-t1
    return near_spots

def _spot_nearby_get(point):
    near_spots = _nearby_spots_find(point, max_spots=50, max_dist=100000)
    #print u'%8.1f m: found %d Spots' % (CURR_DIST, res_cnt)
    features = []
    for p in near_spots:
        features.append(make_feature(p, p.geography, {'name': 'Spot', 'title': u'%s %.5f %.5f' % (p.name, p.geography.coords[1], p.geography.coords[0])}))
    data = { 'geojson': make_featurecollection(features) }
    return data

def spot_nearby_get(request):
    """
    API call to
    """
    req_data = request.REQUEST
    lat = req_data.get('lat')
    lon = req_data.get('lon')
    point = None
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
            point = Point(lon, lat)
            # print point
            data = _spot_nearby_get(point)
            message = u'Spots found'
            return True, data, message
        except ValueError, e:
            logger.debug(u"%s (%s,%s)" % (e, lat, lon))
            data, message = {}, u'Invalid values for "lat" or "lon".'
            return False, data, message
    else:
        data, message = {}, u'No "lat" or "lon" parameters found.'
        return False, data, message

POST_CALLS = {
    'spot_nearby_get': spot_nearby_get,
}
