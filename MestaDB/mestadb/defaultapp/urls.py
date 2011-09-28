# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings
import views

# In default case this is the root url configuration file
urlpatterns = patterns('',
    url(r'^/?$', views.index, name='defaultapp_index'),
    url(r'^login/?$', views.index, name='defaultapp_login'),
    url(r'^logout/?$', views.logout, name='defaultapp_logout'),
)

# Include all other applications via mestadb.urls
urlpatterns += patterns('',
    (r'^', include('mestadb.urls')), # Common stuff is imported here
)
