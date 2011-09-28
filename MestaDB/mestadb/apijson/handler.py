# -*- coding: utf-8 -*-
"""
:mod:`mestadb.api.handler` module forwards request object to appropriate
function and wraps response data into HttpResponse object, possibly
in compressed form.
"""

import django.http
from django.utils.translation import ugettext as _
import json
import zlib
import datetime
from django.contrib.auth.models import User

def login_required(fn):
    """
    @login_required decorator for API functions.
    Checks to see if the user is logged in, if not, return error.
    """
    def _dec(view_func):
        def _checklogin(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)
            else:
                return False, {}, _(u'Login required')
        _checklogin.__doc__ = view_func.__doc__
        _checklogin.__dict__ = view_func.__dict__
        return _checklogin
    return _dec(fn)

def error_response(msg):
    return { 'status': 'error', 'message': msg }

def ok_response(msg, data = {}):
    if data is None:
        data = {}
    data.update({ 'status': 'ok', 'message': msg })
    return data #{ 'status': 'ok', 'message': msg}

def encode_content(request, response, data):
    """
    Check the request for which content encodings client supports.
    zlib.compress(data) if
    - client accepts encoding "deflate"
    - response data length is more than 200 bytes
    Manipulate response headers if necessary.
    In the future this may support some kind of encryption.
    """
    deflate_ok = request.META.get("HTTP_ACCEPT_ENCODING", "").find("deflate") >= 0
    if len(data) > 200 and deflate_ok:
        data = zlib.compress(data)
        response["Content-Encoding"] = "deflate"
    response["Content-Type"] = "application/json"
    return response, data

def get_response_object(request, data):
    """Get the HttpResponse object and write data into it."""
    response = django.http.HttpResponse()
    response, data = encode_content(request, response, data)
    response.write(data)
    response["Content-Length"] = len(data)
    return response, data

def handle_api_call(request, GET_CALLS, POST_CALLS):
    """
    Checks that request method is POST or GET,
    request contains parameter 'operation' and it is valid.
    Returns django.http.HttpResponse object.
    If an API function returns HttpResponse it is returned "as is".
    Plain strings are written into HttpResponse without modification and
    dicts and lists are JSONized before writing into HttpResponse.
    """
    operation = request.REQUEST.get("operation")
    success = False
    data = {}
    if operation is None:
        # TODO: add example how to get help, e.g. operation = "help"
        message = _("'operation' is not defined")
    else:
        if request.method == 'POST' and 'operation' in request.POST:
            if operation in POST_CALLS:
                success, data, message = POST_CALLS[operation](request)
            else:
                message = _("Unknown POST operation '%s'" % operation)
        elif request.method == 'GET' and 'operation' in request.GET:
            if request.GET["operation"] in GET_CALLS:
                success, data, message = GET_CALLS[operation](request)
            else:
                message = _("Unknown GET operation '%s'" % operation)
        else:
            message = _("Illegal request method '%s'" % request.method)
    if isinstance(data, django.http.HttpResponse):
        response = data # Pass HttpResponses "as is"
    elif isinstance(data, basestring): # data is a plain str or unicode
        response, responsedata = get_response_object(request, data)
    else: # Convert data to JSON string
        if success:
            data = ok_response(message, data)
        else:
            data = error_response(message)
        json_data = json.dumps(data,
                               indent = 1,
                               encoding='utf-8',
                               ensure_ascii=True)
        response, responsedata = get_response_object(request, json_data)
        # print data
    return response
