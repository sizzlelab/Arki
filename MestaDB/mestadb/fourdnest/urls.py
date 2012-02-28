# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings

import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='fourdnest_index'),
    url(r'^upload/$', views.simple_upload, name='fourdnest_simple_upload'),
    url(r'^postcomment/$', views.post_comment, name='fourdnest_post_comment'),
    url(r'^help/$', views.mobile_help, name='fourdnest_mobile_help'),
)

from fourdnest.apitastypie import UserResource
from fourdnest.apitastypie import TagResource
from fourdnest.apitastypie import EggResource
from tastypie.api import Api

v1_api = Api(api_name='v1')
v1_api.register(TagResource())
v1_api.register(EggResource())
v1_api.register(UserResource())

urlpatterns += patterns('',
    url(r'^api/v1/egg/upload/?$', views.api_upload, name='fourdnest_api_upload'),
    (r'^api/', include(v1_api.urls)),
    (r'^feeds/georss/?$', views.georss),
)
