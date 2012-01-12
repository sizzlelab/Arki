# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.template import Context
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode, force_unicode
from django.core.urlresolvers import reverse
#from django.db.models import Avg, Max, Min, Count, Sum
from django.db.models import Q

from django.contrib.gis.geos import Point

import os
import StringIO
import tempfile
import PIL
import json

# TODO: check where these belong
# For authorization.
import hmac
import base64
import hashlib


from content.filehandler import handle_uploaded_file
from content.models import Content
from fourdnest.models import Egg, Tag
from forms import UploadForm#, SearchForm, ContentModelForm

# TODO: move this elsewhere, e.g. to apitastypie.py
from django.views.decorators.csrf import csrf_exempt


def _render_to_response(request, template, variables):
    """
    Wrapper for render_to_response() shortcut.
    Puts user, perms and some other common variables available in template.
    """
    variables['request'] = request
    #variables['uploadform'] = UploadForm()
    #variables['searchform'] = SearchForm(request.GET)
    return render_to_response(template, variables,
                              context_instance=RequestContext(request),
                             )

"""
login/logout
POST/PUT/DELETE/UPDATE EGG
COMMENT EGG

"""

def index(request):
    """
    Renders the index page of Fourdnest
    """
    latest_objects = Egg.objects.all()
    latest_objects = latest_objects.order_by('-id')[:30]
    return _render_to_response(request, 'fourdnest_base.html', {
        'latest_objects': latest_objects,
    })

def validate_authorization(request):
    REQUEST_METHOD = request.method
    REQUEST_URI = request.path
    CONTENT = 'foobar' #request.read() # Should exist in PUT request too
    CONTENT_TYPE = request.META['CONTENT_TYPE']
    DATE = request.META['HTTP_DATE']
    message = "\n".join([REQUEST_METHOD,
                         CONTENT, CONTENT_TYPE,
                         DATE,
                         REQUEST_URI])
    print message
    key = 'secret'
    hash = hmac.new(key, message, hashlib.sha1)
    encoded = base64.b64encode( hash.hexdigest() )
    print request.META['HTTP_AUTHORIZATION'], encoded

def validate_4dnest_authorization(request, file_md5_sums):
    """
    Check that Authorization header validates.
    """
    BUFFER_SIZE = 4096
    REQUEST_METHOD = request.method
    REQUEST_URI = request.path.encode('utf8') # for some reason request.path is unicode string
    CONTENT_MD5 = ""
    CONTENT_TYPE = request.META.get('CONTENT_TYPE')
    DATE = request.META.get('HTTP_DATE')
    X_4DNEST_MULTIPARTMD5 = request.META.get('HTTP_X_4DNEST_MULTIPARTMD5')
    fourdnest_multipart_md5_b64 = ''

    if X_4DNEST_MULTIPARTMD5:
        hashes = []
        digest_maker = hashlib.md5()
        keys = request.POST.keys()
        keys.sort() # Put keys to alphabethical order for easier fourdnest_md5 calculation
        print "LOOPING POST DATA:"
        for key in keys:
            value = request.POST[key]
            print "GOT:", key, value
            hashes.append(hashlib.md5(value).hexdigest())
        hashes += file_md5_sums
        fourdnest_multipart_md5 = hashlib.md5("".join(hashes)).hexdigest()
        fourdnest_multipart_md5_b64 = base64.b64encode(fourdnest_multipart_md5)
    #m = hashlib.md5()
    #m.update(raw_post_data)
    #print file_md5_sums
    print "\n\nHASHES: ",hashes
    message = "\n".join([REQUEST_METHOD,
                         CONTENT_MD5,
                         fourdnest_multipart_md5_b64,
                         CONTENT_TYPE,
                         DATE,
                         REQUEST_URI])
    key = 'secret'
    hash = hmac.new(key, message, hashlib.sha1)
    encoded = base64.b64encode(hash.hexdigest())
    print request.META
    if 'HTTP_AUTHORIZATION' in request.META:
        #username, signature = request.META['HTTP_AUTHORIZATION'].split(':')

        auth = request.META['HTTP_AUTHORIZATION'].split(':')
        if len(auth) == 2 and auth[1] == encoded:
            print "AUTH SUCCESSFUL"
            return True
    print "AUTH FAILED"
    return True
    #return False


@csrf_exempt
def api_upload(request):
    """
    Renders the upload form page.
    """
    try:
        if request.method == 'POST': # If the form has been submitted...
            #for header in request.META.keys():
            #    if header.startswith('HTTP'):
            #        print header, request.META[header]
            #print request.raw_post_data[:1000]
            #if request.user.is_authenticated() is False:
            #    return HttpResponse(status=401)
            form = UploadForm(request.POST, request.FILES) # A form bound to the POST data
            #validate_authorization(request)
            if form.is_valid(): # File was posted with form
                c = None
                data = dict(request.POST)
                if request.POST.get('data'):
                    try: # data is a json string containing the same keys as multipart form
                        data = json.loads(request.POST.get('data'))
                    except: # if it was not valid json, use normal post data
                        data = dict(request.POST)
                        #raise
                SUPPORTED_FIELDS = ['title', 'caption', 'author']
                kwargs = {}
                for field in SUPPORTED_FIELDS:
                    kwargs[field] = data.get(field)
                try:
                    kwargs['point'] = Point(float(data.get('lon')), float(data.get('lat')))
                except:
                    #raise
                    pass
                print kwargs
                response_status = 201 # Created
                e = Egg(**kwargs)
                for filefield, tmpname in handle_uploaded_file(request):
                    print "HANDLING FILE:", filefield, tmpname
                    c = Content(**kwargs)
                    originalname = str(request.FILES["file"])
                    # c.user = request.user # Only authenticated users can use this view
                    c.set_file(originalname, tmpname) # Save uploaded file to filesystem
                    digest_maker = hashlib.md5()
                    with open(c.file.path, 'rb') as f:
                        buf = f.read(4096)
                        while buf:
                            digest_maker.update(buf)
                            buf = f.read(4096)
                    file_md5_sums = [digest_maker.hexdigest()]
                    #print digest_maker.hexdigest()
                    if validate_4dnest_authorization(request, file_md5_sums) == True:
                        response_status = 201 # Created
                    else:
                        response_status = 401 # Unauthorized
                    c.get_type_instance() # Create thumbnail if it is supported
                    c.save()
                    e.content = c
                    e.uid = c.uid
                    break # We save only the first file
                e.save()
                response = HttpResponse(status=response_status)
                #response.status_code = 201
                # FIXME: use reverse()
                #return HttpResponseRedirect(reverse('egg api', args=[e.uid]))
                response['Location'] = '/fourdnest/api/v1/egg/%s/' % e.uid
                return response
            else:
                response = HttpResponse(status=204)
                return response
        else:
            raise Http404
    except Exception, err:
        print err
        raise
        return HttpResponse("Server error", status=500)


