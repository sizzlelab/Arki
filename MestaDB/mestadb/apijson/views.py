# -*- coding: utf-8 -*-
"""
:mod:`api.views` imports necessary modules to handle all possible API calls.
"""

# Python modules
import traceback
import time
import os

# Django modules
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.core.context_processors import csrf

# Django 1.3 CSRF stuff
from django.views.decorators.csrf import csrf_exempt

import apijson.handler
import logging
logger = logging.getLogger('django')

"""
Dict (*_CALLS) must contain API operations as keys and
valid function references as values.
"""

POST_CALLS = {}
import authentication
POST_CALLS.update(apijson.authentication.POST_CALLS)

# Load dynamically all API functions from apps
apps = list(settings.CUSTOM_APPS)
for app in apps:
    try:
        if app != 'apijson':
            api_module = __import__('%s.api' % app)
            POST_CALLS.update(api_module.api.POST_CALLS)
            logger.info(u'Successfully imported API from %s' % app)
    except ImportError, e:
        logger.warning("No api module in %s" % app)
    except AttributeError, e:
        logger.warning("No POST_CALLS in module %s.api" % app)

LOCAL_POST_CALLS = {}
POST_CALLS.update(LOCAL_POST_CALLS)

GET_CALLS = {}
if settings.DEBUG is True:
    GET_CALLS = POST_CALLS

# csrf_exempt is here now, because I haven't figured out
# how it could be used from remote non-html/ajax mobile client
@csrf_exempt
def handle_api_call(request):
    """
    Do the actual API call. Catch possible exceptions, which will cause
    ERROR 500 and save the traceback to a file. Return HttpResponse.
    """
    try:
        response = apijson.handler.handle_api_call(request, GET_CALLS, POST_CALLS)
    except Exception, e:
        logger.exception(e)
        raise # because Django handles errors by itself
    return response

def csrf_token(request):
    """Return csrf_token"""
    return HttpResponse(csrf(request)['csrf_token'])

#@login_required
@csrf_exempt
def apitest(request):
    post = []
    get = []
    files = []
    meta = []
    for key in request.POST:
        post.append(u"%s=%s" % (key, request.POST[key]))
    for key in request.GET:
        get.append(u"%s=%s" % (key, request.GET[key]))
    for key in request.FILES:
        files.append(u"%s=%s" % (key, request.FILES[key]))
    for key in request.META:
        meta.append(u"%s=%s" % (key, request.META[key]))
    text = u"""\nPOST:\n%s\nGET:\n%s\nFILES:\n%s\n""" % ("\n".join(post),
                                                         "\n".join(get),
                                                         "\n".join(files))
    response = HttpResponse(text)
    response['Content-Type'] = 'text/plain'
    return response
