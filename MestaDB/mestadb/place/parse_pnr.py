# -*- coding: utf-8 -*-
"""
Simple parser for Finnish Paikannimet 1:20 000 data, e.g. 'PNR_2010_01.TXT'
http://www.maanmittauslaitos.fi/node/6405?sid=1264

File contains lines like this:

Töölönlahti;1;suomi;415;Vakaveden osa;6674725;2552012;6676144;3385531;6673342;385408;091;Helsinki - Helsingfors;011;Helsinki - Helsingfors;01;Uusimaa - Nyland;1;Etelä-Suomi - Södra Finland;1;Etelä-Suomi - Södra Finland;203406A;19O4A1;L4133B3;1;Virallinen kieli;1;Enemmistön kieli;1;Maastotietokanta;10342551;40342551
Tölöviken;2;ruotsi;415;Vakaveden osa;6674725;2552012;6676144;3385531;6673342;385408;091;Helsinki - Helsingfors;011;Helsinki - Helsingfors;01;Uusimaa - Nyland;1;Etelä-Suomi - Södra Finland;1;Etelä-Suomi - Södra Finland;203406A;19O4A1;L4133B3;1;Virallinen kieli;2;Vähemmistön kieli;1;Maastotietokanta;10342551;40342552

If same placeid is found more than once, the version with langcode '1' is preferred.

"""
import sys
sys.path.append('.')

import django.db
from django.contrib.gis.geos import Point
from django.contrib.gis.geos import fromstr
from place.models import Realm, Spot
import time

# Field-name map
fieldname = {
    0: 'name',
    1: 'langcode',
    3: 'type',
    4: 'typetext',
#    7: 'kkj_y', # 200 m error to east when transforming these from srid=2393 to WGS-84/srid=4326
#    8: 'kkj_x',
    9: 'utm_y', # This should be srid=3067
    10: 'utm_x',
    11: 'citycode',
    12: 'cityname',
    30: 'placeid',
    31: 'placenameid',
}

def parse_line(line):
    # Convert line to a list of unicode strings
    fields = [s.decode('latin-1') for s in line.split(';')]
    # Create dict from useful data
    data = {}
    for i in range(len(fields)):
        if i in fieldname:
            data[fieldname[i]] = fields[i]
    data['point'] = fromstr('POINT(%(utm_x)s %(utm_y)s)' % data, srid=3067)
    data['point'].transform(4326) # Transform to WGS84
    return data

@django.db.transaction.commit_manually
def parse_pnr_file(filename, realm):
    """    """
    i = new = updated = old = 0
    start_time = last_time = time.time()
    with open(filename, 'rt') as f:
        for line in f.xreadlines():
            data = parse_line(line)
            #print data
            id = int(data['placeid'])
            if Spot.objects.filter(id=id).count() == 0:
                s = Spot(realm=realm, id=id, name=data['name'], description=data['typetext'])
                s.geography = data['point']
                s.save()
                new += 1
            elif data['langcode'] == u'1':
                # Spot exists, but this one with langcode 1 (Finnish) overrides it
                s = Spot.objects.get(id=id)
                s.name = data['name']
                s.description = data['typetext']
                s.geography = data['point']
                s.save()
                updated += 1
            else:
                # Spot exists, but this one won't override it because of langcode != 1
                old += 1
                so = Spot.objects.filter(id=id)[0]
                print so.id, so.name, id, data['name']
            i += 1
            if i % 1000 == 0: # Commit once in a while
                django.db.transaction.commit()
                print "Commit %d (%d/%d/%d) %.6f" % (i, new, updated, old, time.time() - last_time)
                last_time = time.time()
                django.db.reset_queries() # Needed to empty django.db.connection.queries list
        return i

if __name__ == '__main__':
    # Create a realm for PNR data
    Realm.objects.filter(name='pnr').delete()
    realm = Realm(name='pnr')
    realm.save()
    print parse_pnr_file(sys.argv[1], realm)
