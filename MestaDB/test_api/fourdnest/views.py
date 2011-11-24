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
    #print request.FILES
    for inputfile in request.FILES:
        digest_maker = hashlib.md5()
        filedata = request.FILES[inputfile]
        destination_filename = os.path.join(UPLOAD_DIR, filedata.name)
        with open(destination_filename, 'wb') as destination:
            #print dir(filedata)
            #print filedata.size
            #print filedata.readlines()
            for chunk in filedata.chunks():
                destination.write(chunk)
                digest_maker.update(chunk)
        yield inputfile, destination, digest_maker.digest()

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
    CONTENT_TYPE = request.META.get('CONTENT_TYPE')
    DATE = request.META.get('HTTP_DATE')
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
        for key in keys:
            value = request.POST[key]
            #print "GOT:", key, value
            hashes.append(hashlib.md5(value).digest())
        hashes += file_md5_sums
        fourdnest_multipart_md5 = hashlib.md5("".join(hashes)).digest()
        fourdnest_multipart_md5_b64 = base64.b64encode(fourdnest_multipart_md5)
    #m = hashlib.md5()
    #m.update(raw_post_data)
    message = "\n".join([REQUEST_METHOD,
                         CONTENT_MD5,
                         fourdnest_multipart_md5_b64,
                         CONTENT_TYPE,
                         DATE,
                         REQUEST_URI])
    key = 'secret'
    hash = hmac.new(key, message, hashlib.sha1)
    encoded = base64.b64encode(hash.digest())
    if 'HTTP_AUTHORIZATION' in request.META:
        #username, signature = request.META['HTTP_AUTHORIZATION'].split(':')

        auth = request.META['HTTP_AUTHORIZATION'].split(':')
        if len(auth) == 2 and auth[1] == encoded:
            return True
    return False


@csrf_exempt
def api_upload(request):
    """
    Dummy upload handler for testing purposes.
    """
    #print request.raw_post_data
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
        file_md5_sums = []
        for filefield, tmpname, file_md5 in handle_uploaded_file(request):
            file_md5_sums.append(file_md5)
            print "Field name: '%s', saved to %s" % (filefield, tmpname)
        # FIXME: this doesn't work correctly, because accessing request.FILES empties raw_post_data
        print "AUTHORIZATION SUCCESSFUL:", validate_4dnest_authorization(request, file_md5_sums)
        response = HttpResponse(status=201)
        response['Location'] = '/fourdnest/api/v1/egg/%s/' % 'some_random_uid_would_be_here'
        return response
    else:
        return HttpResponse(status=405) # Method not allowed
