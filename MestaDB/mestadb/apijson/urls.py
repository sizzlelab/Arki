from django.conf.urls.defaults import *
from django.conf import settings

from apijson.views import handle_api_call
from apijson.views import apitest
import authentication

urlpatterns = patterns('',
    (r'^/?$', handle_api_call),
    (r'^csrf_token/?$', authentication.csrf_token),
    (r'^test/?$', apitest),
)
