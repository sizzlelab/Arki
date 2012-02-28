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
import urllib

# TODO: check where these belong
# For authorization.
import hmac
import base64
import hashlib


from content.filehandler import handle_uploaded_file
from content.models import Content
from fourdnest.models import Egg, Tag, Comment
from forms import UploadForm
from forms import MessageForm
from forms import EggForm
from forms import CommentForm

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
    messageform = MessageForm()
    if request.method == 'POST': # If the form has been submitted...
        form = MessageForm(request.POST, request.FILES) # A form bound to the POST data
        if form.is_valid(): # File was posted with form
            e = Egg(caption=form.cleaned_data.get('message'))
            e.user = request.user if request.user.is_authenticated() else None
            e.save()
            return HttpResponseRedirect(reverse('fourdnest_index'))
    latest_objects = Egg.objects.all()
    latest_objects = latest_objects.order_by('-id')[:30]

    for obj in latest_objects:
        if obj.content:
            _, obj.fileext = os.path.splitext(obj.content.originalfilename)
    return _render_to_response(request, 'fourdnest_base.html', {
        'latest_objects': latest_objects,
        #'latest_object_form': latest_object_form,
        'messageform': messageform,
        'cf': CommentForm(),
    })

def mobile_help(request):
    """
    Renders the help page of Fourdnest
    """
    return _render_to_response(request, 'fourdnest_help.html', {
    })

def post_comment(request):
    """
    Save comments.
    """
    commentform = CommentForm()
    if request.method == 'POST': # If the form has been submitted...
        user =  request.user if request.user.is_authenticated() else None
        commentform = CommentForm(request.POST, request.FILES) # A form bound to the POST data
        if commentform.is_valid(): # File was posted with form
            egg_uid = commentform.cleaned_data.get('egg_uid')
            egg = Egg.objects.get(uid=egg_uid)
            comment = Comment(
                user=user,
                text=commentform.cleaned_data.get('comment'),
                egg=egg,
            )
            comment.save()
        else:
            print "NOT VALID COMMENT"
            # TODO add message or something here
    return HttpResponseRedirect(reverse('fourdnest_index', args=[]))

@csrf_exempt
def simple_upload(request):
    """
    Handles uploaded files
    """
    try:
        if request.method == 'POST': # If the form has been submitted...
            user =  request.user if request.user.is_authenticated() else None
            form = UploadForm(request.POST, request.FILES) # A form bound to the POST data
            if form.is_valid(): # File was posted with form
                c = None
                kwargs = {}
                kwargs['author'] = user.username.title() if user else 'Anonymous'
                # Create a new Egg
                e = Egg(**kwargs)
                print kwargs
                for filefield, tmpname in handle_uploaded_file(request):
                    print "HANDLING FILE:", filefield, tmpname
                    c = Content(**kwargs)
                    originalname = str(request.FILES["file"])
                    # c.user = request.user # Only authenticated users can use this view
                    c.set_file(originalname, tmpname) # Save uploaded file to filesystem
                    c.get_type_instance() # Create thumbnail if it is supported
                    c.save()
                    e.content = c
                    e.uid = c.uid
                    break # We save only the first file
                if c:
                    c.user = user
                    c.save()
                e.user = user
                print "USER", user
                if user:
                    response_status = 200 # Created
                else:
                    response_status = 401 # Unauthorized
                e.save()
                # We can handle tags after egg has id (it is saved)
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
    #BUFFER_SIZE = 4096
    # Get authorization stuff from headers
    try:
        username, signature = [unicode(x) for x in request.META['HTTP_AUTHORIZATION'].split(':')]
        username = urllib.unquote(username)
        username = username.strip()
    except (ValueError, KeyError):
        username, signature = '', ''
    try:
        user = User.objects.get(username=username)
        secret_key = (user.last_name or '').encode('ascii') # FIXME: horrible kludge, secret key is in last_name field!
        print "USER_FOUND=%s, HAS_KEY=%s" % (user, secret_key)
    except User.DoesNotExist:
        user = None
        secret_key = 'secret' # Must be ASCII
        print "USER_NOT_FOUND=%s" % (username)
    REQUEST_METHOD = request.method
    REQUEST_URI = request.path.encode('utf8') # for some reason request.path is unicode string
    CONTENT_MD5 = ""
    CONTENT_TYPE = request.META.get('CONTENT_TYPE', '')
    DATE = request.META.get('HTTP_DATE', '')
    X_4DNEST_MULTIPARTMD5 = request.META.get('HTTP_X_4DNEST_MULTIPARTMD5', '')
    fourdnest_multipart_md5_b64 = ''
    hashes = []

    if X_4DNEST_MULTIPARTMD5:
        digest_maker = hashlib.md5()
        keys = request.POST.keys()
        keys.sort() # Put keys to alphabethical order for easier fourdnest_md5 calculation
        print "POST DATA:"
        for key in keys:
            value = request.POST[key]
            print "%s=%s" % (key, value.encode('utf8'))
            hashes.append(hashlib.md5(value.encode('utf8')).hexdigest())
        hashes += file_md5_sums
        fourdnest_multipart_md5 = hashlib.md5("".join(hashes)).hexdigest()
        fourdnest_multipart_md5_b64 = base64.b64encode(fourdnest_multipart_md5)
    #print file_md5_sums
    print "\n\nHASHES: ",hashes
    CONTENT_TYPE = ''
    message = u"\n".join([REQUEST_METHOD,
                         CONTENT_MD5, # Empty string
                         fourdnest_multipart_md5_b64,
                         CONTENT_TYPE, # Empty string
                         DATE,
                         REQUEST_URI])
    #print request.META
    print "MESSAGE TO SIGN:\n-----------------------\n", message
    print "-----------------------"
    hash = hmac.new(secret_key, message, hashlib.sha1)
    encoded = base64.b64encode(hash.hexdigest())
    if user and signature == encoded:
        print "AUTH_SUCCESSFUL_FOR=%s" % user
    else:
        print "AUTH_FAILED_FOR=%s" % user
    return user


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
                jsondata = request.POST.get('data')
                if jsondata is None: # Temporary fix for ambiguous parameter name data / metadata
                    jsondata = request.POST.get('metadata')
                if jsondata:
                    try: # data is a json string containing the same keys as multipart form
                        data = json.loads(jsondata)
                    except: # if it was not valid json, use normal post data
                        data = dict(request.POST)
                        #raise
                SUPPORTED_FIELDS = ['title', 'caption', 'author']
                kwargs = {}
                for field in SUPPORTED_FIELDS:
                    kwargs[field] = data.get(field, '')
                try:
                    kwargs['point'] = Point(float(data.get('lon')), float(data.get('lat')))
                except:
                    kwargs['point'] = None
                    #raise
                    pass
                # Create a new Egg
                e = Egg(**kwargs)
                print kwargs
                response_status = 201 # Created

                tags = data.get('tags')
                if tags:
                    tags = [x.lower() for x in tags]
                    tag_str = ','.join(tags)
                else:
                    tags = []
                    tag_str = ''
                user = c = None
                file_md5_sums = []
                for filefield, tmpname in handle_uploaded_file(request):
                    print "HANDLING FILE:", filefield, tmpname
                    c = Content(**kwargs)
                    c.keywords = tag_str
                    originalname = str(request.FILES["file"])
                    # c.user = request.user # Only authenticated users can use this view
                    c.set_file(originalname, tmpname) # Save uploaded file to filesystem
                    digest_maker = hashlib.md5()
                    with open(c.file.path, 'rb') as f:
                        buf = f.read(4096)
                        while buf:
                            digest_maker.update(buf)
                            buf = f.read(4096)
                    file_md5_sums.append(digest_maker.hexdigest())
                    #print digest_maker.hexdigest()
                    c.get_type_instance() # Create thumbnail if it is supported
                    c.save()
                    # Copy coordinates from content (parsed while saving it if they existed)
                    e.content = c
                    if e.point is None and c.point:
                        e.point = c.point
                    e.uid = c.uid
                    break # We save only the first file
                # Handle authorization after files are handled
                user =  validate_4dnest_authorization(request, file_md5_sums)
                if c:
                    c.user = user
                    c.save()
                e.user = user
                print "USER", user
                if user:
                    response_status = 201 # Created
                else:
                    response_status = 401 # Unauthorized
                e.save()
                # We can handle tags after egg has id (it is saved)
                #print "LOOPING TAGS"
                for tagname in tags:
                    try:
                        tag = Tag.objects.get(name=tagname)
                        #print "Tag old:",
                    except Tag.DoesNotExist:
                        tag = Tag(name=tagname)
                        tag.save()
                        #print "Tag new:",
                    #print tagname, tag
                    e.tags.add(tag)
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


from django.contrib.gis.feeds import GeoRSSFeed
from django.utils.text import truncate_words
import datetime
import time

def datetime2utc(dt):
    """
    Take naive datetime (i.e. from DateTimeField) and
    return it in UTC time. Use this only when converting timestamps in feeds.
    """
    t = time.gmtime(time.mktime(dt.timetuple()))
    dt_utc = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    return dt_utc

def _create_feed(request, feed, url):
    host = "http://" + request.get_host()
    #print host + url
    f = feed(title=u"4Dnest GeoRSS Feed",
         link = host + url,
         feed_url = host + url,
         description = u"4Dnest Demo GeoRSS FEED",
         language = u"fi")
#    qset = Q(privacy = 'PUBLIC')
#    if request.user.is_authenticated():
#        qset |= Q(privacy = 'RESTRICTED')
#        qset |= Q(user = request.user)
#    if feed == GeoRSSFeed:
#        qset &= (Q(point__isnull=False))
#    itemlist = Content.objects.filter(qset)
    itemlist = Content.objects.exclude(point__isnull=True)
    for c in itemlist.order_by("-id")[:30]:
        summary = u"""<a href='%s/content/instance/%s-400x400.jpg'>
          <img src='%s/content/instance/%s-200x200.jpg'/>
          </a><br/>\n%s\n""" % (host, c.uid, host, c.uid, c.caption)
        gmtime = datetime2utc(c.created)
        f.add_item(title = u"%s: %s" % (c.author, truncate_words(c.caption, 4)),
         link = u"%s/content/%s" % (host, c.uid),
         description = summary,
         author_name = c.author,
         item_copyright = c.author,
         author_email = u"4dnest@4dnest.org.invalid",
         author_link = u"http://4dnest.org",
         pubdate = gmtime,
         unique_id = '%s/instance/%s-200x200.jpg' % (host, c.uid),
         #geometry=c.point.coords,
         )
        if c.point:
            f.items[-1]['geometry'] = c.point.coords
    #print dir(f)
    #print f.rss_attributes()
    #print f.items
    return HttpResponse(f.writeString('UTF-8'), mimetype='application/xml')

def georss(request):
    return _create_feed(request, GeoRSSFeed, '/fourdnest/feeds/georss/')

