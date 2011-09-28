from django.conf.urls.defaults import *
from django.conf import settings

from apijson import views

urlpatterns = patterns('',
    (r'^/?$', views.handle_api_call),
    (r'^csrf_token/?$', views.csrf_token),
    (r'^test/?$', views.apitest),
)
