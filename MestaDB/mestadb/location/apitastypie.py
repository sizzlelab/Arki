# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import url
from django.contrib.gis.geos import Point

from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization
from tastypie import fields
from tastypie.bundle import Bundle

from location.models import Entity


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
        filtering = {
            'username': ALL,
        }


class EntityResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = Entity.objects.all()
        resource_name = 'entity'
        authorization = Authorization()
        fields = ['uid', 'name', 'created', 'updated']
        filtering = {
            'user': ALL_WITH_RELATIONS,
            #'created': ['exact', 'lt', 'lte', 'gte', 'gt'],
        }

    def hydrate(self, bundle):
        lat = bundle.data['lat']
        lon = bundle.data['lon']
        bundle.obj.geography = Point(lon, lat)
        return bundle

    def dehydrate(self, bundle):
        """Additional fields, not found in object, perhaps need some processing."""
        bundle.data['lat'] = bundle.obj.geography.coords[1]
        bundle.data['lon'] = bundle.obj.geography.coords[0]
        return bundle

    def get_resource_uri(self, bundle_or_obj):
        kwargs = {
            'resource_name': self._meta.resource_name,
        }
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.guid
        else:
            kwargs['pk'] = bundle_or_obj.guid
        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name
        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

    def override_urls(self):
        """Make resource's URL to match guid instead of real PK id,
        See also get_resource_uri above."""
        return [
            url(r"^(?P<resource_name>%s)/(?P<guid>[\w\d\._-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]
