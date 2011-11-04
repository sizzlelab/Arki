from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import fourdnest.views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'test_api.views.home', name='home'),
    # url(r'^test_api/', include('test_api.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    url(r'^fourdnest/api/v1/egg/upload/$', fourdnest.views.api_upload, name='fourdnest_api_upload'),
)
