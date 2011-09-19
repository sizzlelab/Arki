# -*- coding: utf-8 -*-

#from django.contrib import admin
from django.contrib.gis import admin # as admin

from models import Realm
from models import Spot
from models import Area


class RealmAdmin(admin.ModelAdmin):
    search_fields = ('name', 'description', )
    list_display = ('name', 'added', 'updated', )
    ordering = ('name', )

admin.site.register(Realm, RealmAdmin)


class SpotAdmin(admin.OSMGeoAdmin):
    search_fields = ('name', 'description', )
    list_display = ('name', 'added', 'updated', )
    ordering = ('name', )

admin.site.register(Spot, SpotAdmin)


class AreaAdmin(admin.OSMGeoAdmin):
    search_fields = ('name', 'description', )
    list_display = ('name', 'area', 'added', 'updated', )
    ordering = ('name', )

admin.site.register(Area, AreaAdmin)
