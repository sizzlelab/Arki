# -*- coding: utf-8 -*-
import sys
sys.path.append('.')
#sys.path.append('..')
#from django.db import transaction
#from django import db

import django.db


from place.models import Realm, Spot
from django.contrib.gis.geos import Point
import time

Realm.objects.filter(name='geonames').delete()
realm = Realm(name='geonames')
realm.save()

@django.db.transaction.commit_manually
def parse_geonames_file(geonames_file):
    """    """
    i = new = old = 0
    start_time = last_time = time.time()
    f = open(geonames_file, 'rt')
    for line in f.xreadlines():
        t = [unicode(x, 'utf8') for x in line.split('\t')]
        id = int(t[0])
        if Spot.objects.filter(id=id).count() == 0:
            s = Spot(realm=realm, id=id, name=t[1])
            s.geography = Point(float(t[5]), float(t[4]))
            s.save()
            new += 1
        else:
            old += 1
        i += 1
        if i % 1000 == 0:
            django.db.transaction.commit()
            print "Commit %d (%d/%d) %.6f" % (i, new, old, time.time() - last_time)
            last_time = time.time()
            django.db.reset_queries() # Needed to empty django.db.connection.queries list
    f.close()
    return i

if __name__ == '__main__':
    print parse_geonames_file(sys.argv[1])
