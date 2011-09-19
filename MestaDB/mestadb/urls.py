# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
import os

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    (r'^api/', include('apijson.urls')),
    (r'^place/', include('place.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Translation UI
    # url(r'^rosetta/', include('rosetta.urls')),

    # Language change url
    (r'^i18n/', include('django.conf.urls.i18n')),
)

# OBSOLETE since Django 1.3
## This puts all content in /appname/static/* available in static.serve
#for APP in settings.CUSTOM_APPS:
#    pattern = '^static/%s/' % APP + r'(?P<path>.*)$'
#    path = os.path.join(settings.ROOT_DIR, APP, 'static').replace('\\','/')
#    # print pattern, path
#    urlpatterns += patterns('',
#        (pattern, 'django.views.static.serve',
#         {'document_root': path}),
#    )

#urlpatterns += patterns('',
#    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
#     {'document_root': os.path.join(settings.ROOT_DIR, 'media')}),
#    # Enable /static/*
#    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
#     #{'document_root': os.path.join(settings.ROOT_DIR, 'static').replace('\\','/')}),
#     {'document_root': settings.STATIC_DOC_ROOT}),
#)
