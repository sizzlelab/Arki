# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import url
from django.contrib.gis.geos import Point

from django.http import Http404
from django.core.paginator import Paginator, InvalidPage

from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.authentication import Authentication
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.authorization import DjangoAuthorization
from tastypie.utils import trailing_slash

from content.models import Content
from fourdnest.models import Egg, Tag

import os.path

DEFAULT_EGG_OBJECTS = 50

class DjangoAuthentication(Authentication):
    """Authenticate based upon Django session."""
    def is_authenticated(self, request, **kwargs):
        return True
        #return request.user.is_authenticated()

    # Optional but recommended
    def get_identifier(self, request):
        return request.user.username


class LimitByUserAuthorization(Authorization):
    def is_authorized(self, request, object=None):
        #print request.user.id, request.user.is_authenticated(), dir(request.user)
        return True
        #return request.user.is_authenticated()

    # Optional but useful for advanced limiting, such as per user.
    def apply_limits(self, request, object_list):
        return object_list
        #if request and hasattr(request, 'user'):
        #    #print dir(request.user)
        #    #return object_list.filter(user_id=request.user.id)
        #    return object_list.filter(user=request.user)
        #return object_list.none()

class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
        filtering = {
            'username': ALL,
        }
        #authentication = BasicAuthentication()
        authentication = DjangoAuthentication()
        authorization = DjangoAuthorization()
        #authorization = LimitByUserAuthorization()

class TagResource(ModelResource):

    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'tag'
        fields = ['uid', 'name', 'created']
        #authentication = BasicAuthentication()
        authentication = DjangoAuthentication()
        #authorization = Authorization()
        #authorization = DjangoAuthorization()
        authorization = LimitByUserAuthorization()

    def override_urls(self):
        """Make resource's URL to match uid instead of real PK id,
        See also get_resource_uri above."""
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/(?P<uid>[\w\d\._-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def get_resource_uri(self, bundle_or_obj):
        kwargs = {
            'resource_name': self._meta.resource_name,
        }
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.uid
        else:
            kwargs['pk'] = bundle_or_obj.uid
        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name
        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # Do the query.
        objects = Tag.objects.all() # First get default part
        # TODO:
        paginator = Paginator(objects, 20)
        # TODO: paginator from parameters or default 50
        try:
            page = paginator.page(int(request.GET.get('page', 1)))
        except InvalidPage:
            raise Http404("Sorry, no results on that page.")

        objects = []

        for result in page.object_list:
            #print type(result), dir(result)
            #bundle = self.build_bundle(obj=result.object, request=request)
            bundle = self.build_bundle(obj=result, request=request)
            bundle = self.full_dehydrate(bundle)
            #print dir(result)
            objects.append(bundle)

        object_list = {
            'objects': objects,
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)



class EggResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user',  null=True)

    class Meta:
        # Return only Eggs, which are successfully authorized and has user
        queryset = Egg.objects.filter(user__isnull=False).order_by('-created')
        resource_name = 'egg'
        fields = ['uid', 'title', 'caption', 'author', 'created']
        filtering = {
            'user': ALL_WITH_RELATIONS,
            #'created': ['exact', 'lt', 'lte', 'gte', 'gt'],
        }
        #authentication = BasicAuthentication()
        authentication = DjangoAuthentication()
        #authorization = Authorization()
        #authorization = DjangoAuthorization()
        authorization = LimitByUserAuthorization()

    def hydrate(self, bundle):
        try:
            lat = bundle.data['lat']
            lon = bundle.data['lon']
            bundle.obj.point = Point(lon, lat)
        except KeyError, err:
            pass
        except Exception, err:
            print str(err)
            raise
        tags = bundle.data.get('tags', [])
        if tags and isinstance(tags, list):
            tags = [x.lower() for x in tags]
            tag_str = ','.join(tags)
            bundle.obj.tags.clear()
            for tagname in tags:
                try:
                    tag = Tag.objects.get(name=tagname)
                    print "Tag old:",
                except Tag.DoesNotExist:
                    tag = Tag(name=tagname)
                    tag.save()
                    print "Tag new:",
                print tagname, tag
                bundle.obj.tags.add(tag)
            if bundle.obj.content:
                bundle.obj.content.keywords = tag_str
                bundle.obj.content.save()
                # Copy coordinates from content (parsed while saving it if they existed)
                # FIXME: check that obj hasn't already valid point
                #if bundle.obj.content.point:
                #    bundle.obj.point = bundle.obj.content.point
            #print "ON LISTA"
        if bundle.data.get('uid'):
            bundle.obj.uid = bundle.data.get('uid')
        # The owner of Entity is get from request's authenticated user
        if bundle.request.user.is_authenticated():
            bundle.obj.user = bundle.request.user
        return bundle

    def dehydrate(self, bundle):
        """Additional fields, not found in object, perhaps need some processing."""
        if bundle.obj.point:
            bundle.data['lat'] = bundle.obj.point.coords[1]
            bundle.data['lon'] = bundle.obj.point.coords[0]
        if bundle.obj.content and bundle.obj.content.thumbnail():
            bundle.data['thumbnail_uri'] = "/content/instance/%s-100x100.jpg" % bundle.obj.content.uid
        if bundle.obj.content:
            root, ext = os.path.splitext(bundle.obj.content.originalfilename)
            #FIXME: check that ext exists
            bundle.data['content_uri'] = "/content/original/%s%s" % (bundle.obj.content.uid, ext)
        bundle.data['tags'] = [x.name for x in bundle.obj.tags.all()]

        #print dir(bundle.data),
        #print dir(bundle.obj)
        #if hasattr(bundle.obj, 'distance'):
        #    bundle.data['distance'] = bundle.obj.distance
        return bundle

    def get_resource_uri(self, bundle_or_obj):
        kwargs = {
            'resource_name': self._meta.resource_name,
        }
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.uid
        else:
            kwargs['pk'] = bundle_or_obj.uid
        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name
        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

    def override_urls(self):
        """Make resource's URL to match uid instead of real PK id,
        See also get_resource_uri above."""
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/(?P<uid>[\w\d\._-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # Do the query.
        objects = Egg.objects.all().order_by('-created') # First get default part

        #sqs = SearchQuerySet().models(Note).load_all().auto_query(request.GET.get('q', ''))
        paginator = Paginator(objects, DEFAULT_EGG_OBJECTS)
        # TODO: paginator from parameters or default 50
        try:
            page = paginator.page(int(request.GET.get('page', 1)))
        except InvalidPage:
            raise Http404("Sorry, no results on that page.")

        objects = []

        for result in page.object_list:
            #print type(result), dir(result)
            #bundle = self.build_bundle(obj=result.object, request=request)
            bundle = self.build_bundle(obj=result, request=request)
            bundle = self.full_dehydrate(bundle)
            #print dir(result)
            objects.append(bundle)

        object_list = {
            'objects': objects,
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)
