# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
import os

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    (r'^api/', include('apijson.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Translation UI
    # url(r'^rosetta/', include('rosetta.urls')),

    # Language change url
    (r'^i18n/', include('django.conf.urls.i18n')),
)

# Load dynamically all CUSTOM_APPS.urls
for APP in settings.CUSTOM_APPS:
    if APP != 'defaultapp':
        pat = ('^%s/' % APP, include('%s.urls' % APP))
        urlpatterns += patterns('', pat)
