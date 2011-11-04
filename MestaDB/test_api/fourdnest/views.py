# -*- coding: utf-8 -*-

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import os

# For authorization.
import hmac
import base64
import hashlib


UPLOAD_DIR = "uploaded_files"

def handle_uploaded_file(request):
    """
    Save all files found in request.FILES to filesystem.
    """
    if os.path.isdir(UPLOAD_DIR) is False:
        os.mkdir(UPLOAD_DIR)
    print request.FILES
    for inputfile in request.FILES:
        filedata = request.FILES[inputfile]
        destination_filename = os.path.join(UPLOAD_DIR, filedata.name)
        with open(destination_filename, 'wb') as destination:
            for chunk in filedata.chunks():
                destination.write(chunk)
        yield inputfile, destination

def validate_authorization(request):
    """
    Check that Authorization header validates.
    """
    REQUEST_METHOD = request.method
    REQUEST_URI = request.path.encode('utf8') # for some reason request.path is unicode string
    raw_post_data = request.read()
    m = hashlib.md5()
    m.update(raw_post_data)# read() Should exist in PUT request too
    CONTENT_MD5 = m.digest()
    CONTENT_TYPE = request.META['CONTENT_TYPE']
    DATE = request.META['HTTP_DATE']
    message = "\n".join([REQUEST_METHOD,
                         CONTENT_MD5, CONTENT_TYPE,
                         DATE,
                         REQUEST_URI])
    #print message
    key = 'secret'
    hash = hmac.new(key, message, hashlib.sha1)
    encoded = base64.b64encode( hash.digest() )
    if 'HTTP_AUTHORIZATION' in request.META:
        username, signature = request.META['HTTP_AUTHORIZATION'].split(':')
        #print request.META['HTTP_AUTHORIZATION'], encoded
        if signature == encoded:
            return True
    return False


@csrf_exempt
def api_upload(request):
    """
    Dummy upload handler for testing purposes.
    """
    print '--------------------------------------------------------------------'
    if request.method == 'POST': # If the form has been submitted...
        print '----- HTTP HEADERS -----'
        for header in request.META.keys():
            if header.startswith('HTTP') or header in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                print "%s: %s" % (header.replace('HTTP_', ''), request.META[header])
        print '----- HTTP POST DATA -----'
        for field in request.POST.keys():
            print "%s=%s" % (field, request.POST[field])
        #print request.raw_post_data[:1000]
        print '----- HTTP POST FILES -----'
        for filefield, tmpname in handle_uploaded_file(request):
            print "Field name: '%s', saved to %s" % (filefield, tmpname)
        # FIXME: this doesn't work correctly, because accessing request.FILES empties raw_post_data
        #print "AUTHORIZATION SUCCESSFUL:", validate_authorization(request)
        response = HttpResponse(status=201)
        response['Location'] = '/fourdnest/api/v1/egg/%s/' % 'some_random_uid_would_be_here'
        return response
    else:
        return HttpResponse(status=405) # Method not allowed
