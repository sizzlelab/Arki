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
import os.path
import StringIO
import tempfile
import PIL
from PIL import Image, ImageDraw, ImageFont
import json

from filehandler import handle_uploaded_file
from models import Content
from forms import UploadForm, SearchForm, ContentModelForm

"""
TODO: make GeoIP work!
TODO: try to make PyExiv2 work
"""

def _render_to_response(request, template, variables):
    """
    Wrapper for render_to_response() shortcut.
    Puts user, perms and some other common variables available in template.
    """
    variables['request'] = request
    variables['uploadform'] = UploadForm()
    variables['searchform'] = SearchForm(request.GET)
    return render_to_response(template, variables,
                              context_instance=RequestContext(request),
                             )


@login_required
def index(request):
    """
    Renders the index page of Content.
    """
    if request.user.is_superuser:
        latest_objects = Content.objects.all()
    else:
        latest_objects = Content.objects.filter(user=request.user)
    q = request.GET.get('q')
    if q and len(q) >= 2:
        qset = Q(title__icontains = q)
        qset |= Q(caption__icontains = q)
        qset |= Q(mimetype__icontains = q)
        qset |= Q(originalfilename__icontains = q)
        latest_objects = latest_objects.filter(qset)
    latest_objects = latest_objects.order_by('-id')[:20]
    return _render_to_response(request, 'content_base.html', {
        'latest_objects': latest_objects,
    })

@login_required
def upload(request):
    """
    Renders the upload form page.
    """
    if request.method == 'POST': # If the form has been submitted...
        form = UploadForm(request.POST, request.FILES) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            for filefield, tmpname in handle_uploaded_file(request):
                c = Content()
                originalname = str(request.FILES["file"])
                c.user = request.user # Only authenticated users can use this view
                c.set_file(originalname, tmpname) # Save uploaded file to filesystem
                c.get_type_instance() # Create thumbnail if it is supported
                c.save()
            return HttpResponseRedirect(reverse('edit', args=[c.uid]))
    else:
        form = UploadForm(initial={}) # An unbound form
    return _render_to_response(request, 'content_upload.html', {
                                  'uploadform' : form,
                               })

# TODO: move this elsewhere, e.g. to apitastypie.py
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
#@login_required
def api_upload(request):
    """
    Renders the upload form page.
    """
    if request.method == 'POST': # If the form has been submitted...
        #for header in request.META.keys():
        #    if header.startswith('HTTP'):
        #        print header, request.META[header]
        #print request.raw_post_data[:1000]
        if request.user.is_authenticated() is False:
            return HttpResponse(status=401)
        form = UploadForm(request.POST, request.FILES) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            for filefield, tmpname in handle_uploaded_file(request):
                SUPPORTED_FIELDS = ['title', 'caption', 'author']
                kwargs = {}
                for field in SUPPORTED_FIELDS:
                    kwargs[field] = request.POST.get(field)
                try:
                    kwargs['point'] = Point(float(request.POST.get('lon')), float(request.POST.get('lat')))
                except:
                    #raise
                    pass
                print kwargs
                c = Content(**kwargs)
                originalname = str(request.FILES["file"])
                c.user = request.user # Only authenticated users can use this view
                c.set_file(originalname, tmpname) # Save uploaded file to filesystem
                c.get_type_instance() # Create thumbnail if it is supported
                c.save()
                break # We save only the first file
            response = HttpResponse(status=201)
            #response.status_code = 201
            # FIXME: use reverse()
            response['Location'] = '/content/api/v1/content/%s/' % c.uid
            return response
            #return HttpResponseRedirect(reverse('edit', args=[c.uid]))
        else:
            response = HttpResponse(status=204)
            return response
    else:
        raise Http404




@login_required
def html5upload(request):
    """
    Renders the upload form page.
    """
    if request.method == 'POST': # If the form has been submitted...
        result = []
        for filefield, tmpname in handle_uploaded_file(request):
            c = Content()
            originalname = str(request.FILES["file"])
            c.user = request.user # Only authenticated users can use this view
            c.set_file(originalname, tmpname) # Save uploaded file to filesystem
            c.get_type_instance() # Create thumbnail if it is supported
            c.save()
            #print originalname
            #generating json response array
            result.append({"name": originalname,
                           "size": c.filesize,
                           "url": c.uid,
                           "thumbnail_url": '/content/instance/%s-200x200.jpg' % c.uid,
                           "delete_url": '/content/delete/%s' % c.uid,
                           "delete_type":"POST",})
        #print result
        response_data = json.dumps(result)
        #print response_data
        #checking for json data type
        #big thanks to Guy Shapiro
        if "application/json" in request.META['HTTP_ACCEPT_ENCODING']:
            mimetype = 'application/json'
        else:
            mimetype = 'text/plain'
        return HttpResponse(response_data, mimetype=mimetype)
    return _render_to_response(request, 'content_html5upload.html', {
                               })



@login_required
def edit(request, uid):
    """
    Renders the edit form page.
    """
    # Check that object exists and user is allowed to edit it
    try:
        object = Content.objects.get(uid=uid)
    except Content.DoesNotExist:
        raise Http404
    if object.user != request.user and not request.user.is_superuser:
        raise Http404 # FIXME: unauthorized instead
    # Create form instance
    if request.method == 'POST': # If the form has been submitted...
        form = ContentModelForm(request.POST, instance=object)
        if form.is_valid(): # All validation rules pass
            new_object = form.save(commit=False)
            if form.cleaned_data['latlon']:
                lat, lon = [float(x) for x in form.cleaned_data['latlon'].split(',')]
                new_object.point = Point(lon, lat)
                #print lat, lon, new_object.point
            else:
                new_object.point = None
            msg = _(u'Form was saved successfully')
            messages.success(request, msg)
            new_object.save()
            return HttpResponseRedirect(reverse('edit', args=[new_object.uid]))
        #else:
        #    form = UploadForm(initial={}) # An unbound form
    else:
        initial = {}
        if object and object.point:
            initial['latlon'] = u'%.8f,%.8f' % (object.point.coords[1], object.point.coords[0])
        form = ContentModelForm(instance=object, initial=initial)
    return _render_to_response(request, 'content_edit.html', {
                                  'editform' : form,
                                  'object': object,
                               })

@login_required
def search(request):
    form = SearchForm()
    return _render_to_response(request, 'content_search.html', {
                                  'searchform' : form,
                               })


def _get_placeholder_instance(c, text=None):
    imsize = (160, 80)
    immode = 'RGBA'
    imfont = 'Arial.ttf'
    imfontsize = 22
    imtext = c.mimetype if text is None else text
    imtext = imtext.replace('/', ' ').split(' ')
    if len(imtext) == 1:
        imtext.append(u'')
    im = Image.new(immode, imsize, '#eeeeee')
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype(imfont, imfontsize, encoding='unic')
    except IOError:
        font = ImageFont.load_default()
        raise
    
    draw.text((5,10), imtext[0], font=font, fill='#333333')
    draw.text((5,35), imtext[1], font=font, fill='#333333')
    #corners = [(0,0), 
    #           (imsize[0], 0), 
    #           (imsize[0], imsize[1]),
    #           (0, imsize[1]),
    #           (0,0)
    #           ]
    #for i in range(0,len(corners)-1):
    #    draw.line((corners[i], corners[i+1]), width=3, fill='#000000')
    del draw
    #im.save("/tmp/text.png", "PNG")
    return im 

#@cache_page(60 * 60) # FIXME: this value should in settings.py
#@cache_page(60 * 60)
def instance(request, uid, width, height, action, ext):
    """
    Return scaled JPEG instance of the Content, which type is image.
    New size is determined from URL.
    action can be '-crop'
    """
    # w, h = width, height
    response = HttpResponse()
    try:
        c = Content.objects.get(uid=uid)
    except Content.DoesNotExist:
        raise Http404
    if c.mimetype:
        contenttype = c.mimetype.split("/")[0]
    else: # FIXME: no mimetype, content may be broken? Check where contenttype is set and make sure there is some meaningful value always! Perhaps required field?
        contenttype = None
    # Return image if type is image or video
    #if contenttype in ['image', 'video']:
    if True or contenttype in ['image', 'video']:
        thumbnail = None
        if contenttype == 'image':
            thumbnail = c.image.thumbnail
        elif contenttype == 'video':
            thumbnail = c.video.thumbnail
        try:
            im = PIL.Image.open(thumbnail.path)
        except AttributeError, err:
            print "No thumbnail in non-video/image Content ", c.uid, str(err)
            im = _get_placeholder_instance(c)
        except IOError, err:
            print "IOERROR in Content ", c.uid, str(err)
            raise
            return HttpResponse('ERROR: This Content has no thumbnail.', status=404)
        except ValueError, err:
            print "ValueERROR in Content, missing thumbnail:", c.uid, str(err)
            im = _get_placeholder_instance(c, text=u'Missing thumbnail')
            #return HttpResponse('ERROR: This Content has no thumbnail.', status=404)
        size = int(width), int(height)
        if action == '-crop':
            shorter_side = min(im.size)
            side_divider = 1.0 * shorter_side / min(size)
            crop_size = int(max(im.size) / side_divider) + 1
            #print shorter_side, side_divider, im.size, crop_size
            size = (crop_size, crop_size)
            im.thumbnail(size, PIL.Image.ANTIALIAS)
            margin = (max(im.size) - min(im.size)) / 2
            crop_size = min(im.size)
            if im.size[0] > im.size[1]: #horizontal
                crop = [0 + margin, 0, margin + crop_size, crop_size]
            else:
                crop = [0, 0 + margin, crop_size, margin + crop_size]
            im = im.crop(crop)
        else:
            im.thumbnail(size, PIL.Image.ANTIALIAS)
        # TODO: use imagemagick and convert for better quality
        tmp = StringIO.StringIO()
        im.save(tmp, "jpeg", quality=90)
        data = tmp.getvalue()
        tmp.close()
        response = HttpResponse()
        response.write(data)
        response["Content-Type"] = "image/jpeg"
        response["Content-Length"] = len(data)
        if 'attachment' in request.GET:
            response["Content-disposition"] = "attachment; filename=%s-%s.jpg" % (c.originalfilename, c.uid)
        # Use 'opens' time in Last-Modified header (cache_page uses caching page)
        response['Last-Modified'] = c.opens.strftime('%a, %d %b %Y %H:%M:%S GMT')
        return response
    else:
        data = "Requested %s %s %s %s %s " % (c.mimetype, uid, width, height, ext)
        response.write(data)
        response["Content-Type"] = "text/plain" #content_item.mime
        response["Content-Length"] = len(data)
        return response

#@login_required
@cache_page(60 * 60)
def original(request, uid):
    """
    Return original file.
    """
    # FIXME: this doesn't authenticate!
    uid = uid.split('.')[0] # remove possible extension
    try:
        c = Content.objects.get(uid=uid)
    except Content.DoesNotExist:
        raise Http404
    # Return image if type is image or video
    tmp = open(c.file.path, "rb")
    data = tmp.read()
    tmp.close()
    response = HttpResponse()
    response.write(data)
    response["Content-Type"] = c.mimetype
    response["Content-Length"] = len(data)
    return response

@login_required
def metadata(request, uid):
    """
    Return scaled JPEG instance of the Content, which type is image.
    New size is determined from URL.
    """
    response = HttpResponse()
    try:
        c = Content.objects.get(uid=uid)
    except Content.DoesNotExist:
        raise Http404
    data = []
    data.append(u"Author: %s" % c.author)
    data.append(u"Caption: %s" % c.caption)
#    data.append(u"City: %s" %  c.region.all()[0].name)
#    data.append(u"Decade: %s" %  c.decade.all()[0].name)
    data = "\n".join(data)
    response = HttpResponse()
    response.write(data)
    response["Content-Type"] = "text/plain" #content_item.mime
    response["Content-Length"] = len(data)
    response["Content-disposition"] = "attachment; filename=fotorally-%s.txt" % (c.uid)
    return response
