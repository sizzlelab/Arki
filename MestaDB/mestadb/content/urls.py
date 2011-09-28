# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings

import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^search/$', views.search, name='search'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^html5upload/$', views.html5upload, name='html5upload'),
    url(r'^edit/(?P<uid>[\w]+)/$', views.edit, name='edit'),
    url(r'^instance/(?P<uid>[\w]+)-(?P<width>\d+)x(?P<height>\d+)\.(?P<ext>\w+)$', views.instance, name='instance'),
    (r'^original/(\w+)$', views.original),
    (r'^metadata/(\w+)$', views.metadata),
)
