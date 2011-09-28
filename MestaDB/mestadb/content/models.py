# -*- coding: utf-8 -*-
"""
Defines all supported different content type classes (image, video, audio etc.).
If file type is not supported, it is saved "as is".
"""

import os
import re
import time
import hashlib
import mimetypes
import PIL.Image
import string
import random
import datetime
import tempfile

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.gis.geos import *

from content.filetools import get_videoinfo, get_imageinfo, get_mimetype, do_video_thumbnail

content_storage = FileSystemStorage(location=settings.APP_DATA_DIRS['CONTENT'])
preview_storage = FileSystemStorage(location=settings.APP_VAR_DIRS['PREVIEW'])

# define this in local_settings, if you want to change this
try:
    THUMBNAIL_PARAMETERS = settings.CONTENT_THUMBNAIL_PARAMETERS
except:
    THUMBNAIL_PARAMETERS = (1000, 1000, 'JPEG', 90) # w, h, format, quality

def upload_split_by_1000(obj, filename):
    """
    Return the path where the original file will be saved.
    Files are split into a directory hierarchy, which bases on object's id,
    e.g. if obj.id is 12345, fill path will be 000/012/filename
    so there will be max 1000 files in a directory.
    NOTE: if len(id) exeeds 9 (it is 999 999 999) directory hierarchy will
    get one level deeper, e.g. id=10**9 -> 100/000/000/filename
    This should not clash with existings filenames.
    """
    obj.save() # save the object to ensure there is obj.id available
    if hasattr(obj, 'content'):
        id = obj.content.id
    else:
        id = obj.id
    longid = "%09d" % (id) # e.g. '000012345'
    chunkindex = [i for i in range(0, len(longid)-3, 3)] # -> [0, 3, 6]
    path = os.sep.join([longid[j:j+3] for j in chunkindex] + [filename])
    return path

def get_uid(length=12):
    """
    Generate and return a random string which can be considered unique.
    Default length is 12 characters from set [a-zA-Z0-9].
    """
    alphanum = string.letters + string.digits
    return ''.join([alphanum[random.randint(0,len(alphanum)-1)] for i in xrange(length)])

class Content(models.Model):
    """
    Common fields for all content files.
    """
    # Static fields (for internal use)
    id = models.AutoField('ID', primary_key=True)
    status = models.CharField(max_length=40, default="UNPROCESSED", editable=False)
    privacy = models.CharField(max_length=40, default="PRIVATE",
                               choices=(("PRIVATE", "Private"),
                                        ("RESTRICTED", "Restricted"),
                                        ("PUBLIC", "Public")))
    uid = models.CharField(max_length=40, unique=True, db_index=True, default=get_uid, editable=False)
    "Unique identifier for current Content"
    user = models.ForeignKey(User, blank=True, null=True)
    "The owner of this Content (Django User)"
    originalfilename = models.CharField(max_length=256, null=True, editable=False)
    "Original filename of the uploaded file"
    filesize = models.IntegerField(null=True, editable=False)
    "Size of original file"
    filetime = models.DateTimeField(blank=True, null=True, editable=False)
    "Creation time of original file (e.g. EXIF timestamp)"
    mimetype = models.CharField(max_length=200, null=True, editable=False)
    "Official MIME Media Type (e.g. image/jpeg, video/mp4)"
    file = models.FileField(storage=content_storage, upload_to=upload_split_by_1000, editable=False)
    "Actual Content"
    md5 = models.CharField(max_length=32, null=True, editable=False)
    "MD5 hash of original file in hex-format"
    sha1 = models.CharField(max_length=40, null=True, editable=False)
    "SHA1 hash of original file in hex-format"
    added = models.DateTimeField(auto_now_add=True)
    "Timestamp when current Content was added to the system."
    updated = models.DateTimeField(auto_now=True)
    "Timestamp of last update of current Content."
    opens = models.DateTimeField(default=datetime.datetime.now)
    "Timestamp when current Content is available for others than owner."
    expires = models.DateTimeField(blank=True, null=True)
    "Timestamp when current Content is not anymore available for others than owner."

    # Static fields (for human use)
    title = models.CharField(max_length=200, blank=True, null=True)
    "Short title for Content, a few words max."
    caption = models.TextField(blank=True, null=True)
    "Longer description of Content."
    author = models.CharField(max_length=200, blank=True, null=True)
    "Content author's name or nickname."
    keywords = models.CharField(max_length=500, blank=True, null=True)
    "Comma separated list of keywords/tags."
    place = models.CharField(max_length=500, blank=True, null=True)
    "Country, state/province, city, address or other textual description."
    # license
    # origin, e.g. City museum, John Smith's photo album
    # Links and relations to other content files
    peers = models.ManyToManyField("self", blank=True, null=True, editable=True)
    parent = models.ForeignKey("self", blank=True, null=True, editable=True)
    linktype = models.CharField(max_length=500, blank=True, null=True)
    "Information of the type of child-parent relation."
    #point = models.CharField(max_length=500, blank=True, null=True, editable=False)
    point = models.PointField(blank=True, null=True, editable=False)
    objects = models.GeoManager()

    def set_file(self, originalfilename, filecontent, mimetype=None):
        """
        Set Content.file and all it's related fields.
        filecontent may be
        - open file handle (opened in "rb"-mode)
        - existing file name (full path)
        - raw file data
        NOTE: this reads all file content into memory
        """
        if isinstance(filecontent, file):
            filecontent.seek(0)
            filedata = filecontent.read()
        elif len(filecontent) < 1000 and os.path.isfile(filecontent):
            f = open(filecontent, "rb")
            filedata = f.read()
            f.close()
        else:
            filedata = filecontent
        self.originalfilename = os.path.basename(originalfilename)
        self.md5 = hashlib.md5(filedata).hexdigest()
        self.sha1 = hashlib.sha1(filedata).hexdigest()
        self.save() # Must save here to get self.id
        root, ext = os.path.splitext(originalfilename)
        filename = u"%09d-%s%s" % (self.id, self.uid, ext.lower())
        self.file.save(filename, ContentFile(filedata))
        self.filesize = self.file.size
        mime = get_mimetype(self.file.path)
        if mime:
            self.mimetype = mime
        else:
            self.mimetype = mimetypes.guess_type(originalfilename)[0]
        self.save()

    #def save(self, *args, **kwargs):
    #    super(Content, self).save(*args, **kwargs) # Call the "real" save() method.

    def get_type_instance(self):
        """
        Return related Image, Video etc. object.
        If object doesn't exist yet, create new one and return it, if possible.
        """
        if self.mimetype.startswith("image"):
            try:
                return self.image
            except Image.DoesNotExist:
                image = Image(content=self)
                image.save() # Save new instance to the database
                return image
        elif self.mimetype.startswith("video"):
            try:
                return self.video
            except Video.DoesNotExist:
                video = Video(content=self)
                video.save() # Save new instance to the database
                return video
        else:
            return None


    def thumbnail(self):
        """
        Return thumbnail if it exists.
        Thumbnail is always an image (can be shown with <img> tag).
        """
        if self.mimetype is None:
            return None
        if self.mimetype.startswith("image"):
            return self.image.thumbnail
        elif self.mimetype.startswith("video"):
            return self.video.thumbnail
        else:
            return None

    def __unicode__(self):
        text = self.caption[:50] if self.caption else self.title
        return u'"%s" (%s %s B)' % (
                 text, self.mimetype, self.filesize)

class Image(models.Model):
    content = models.OneToOneField(Content, primary_key=True, editable=False)
    width = models.IntegerField(blank=True, null=True, editable=False)
    height = models.IntegerField(blank=True, null=True, editable=False)
    rotate = models.IntegerField(blank=True, null=True, default=0, choices=[(0,0), (90,90), (180,180), (270,270)])
    "Original image must be rotated n degrees CLOCKWISE before showing."
    thumbnail = models.ImageField(storage=preview_storage, upload_to=upload_split_by_1000, editable=False)

    def orientation(self):
        if self.width > self.height:
            return u'horizontal'
        else:
            return u'vertical'

    def __unicode__(self):
        return u"Image: %s (%dx%dpx)" % (
                 self.content.originalfilename,
                 self.width, self.height)

    def generate_thumb(self, image, thumbfield, t):
        """
        TODO: move the general part outside of the model
        """
        if thumbfield:
            thumbfield.delete() # Delete possible previous version
        try:
            im = image.copy()
        except IOError: # Image file is corrupted
            # TODO: use logging! print "ERROR in image file:", self.content.id, self.content.file
            return False
        if im.mode not in ('L', 'RGB'):
            im = im.convert('RGB')
        size = (t[0], t[1])
        if self.rotate == 90:
            im = im.transpose(PIL.Image.ROTATE_270)
        elif self.rotate == 180:
            im = im.transpose(PIL.Image.ROTATE_180)
        elif self.rotate == 270:
            im = im.transpose(PIL.Image.ROTATE_90)
        im.thumbnail(size, PIL.Image.ANTIALIAS)
        # TODO: use imagemagick and convert
        # Save resized image to a temporary file
        # NOTE: the size will be increased if original is smaller than size
        tmp = tempfile.NamedTemporaryFile()
        im.save(tmp, "jpeg", quality=t[3])
        tmp.seek(0)
        data = tmp.read()
        tmp.close()
        postfix = "%s-%s-%sx%s" % (t)
        #filename = u"%09d-%s%s" % (self.id, self.uid, ext.lower())
        filename = u"%09d-%s-%s.jpg" % (self.content.id, self.content.uid, postfix)
        thumbfield.save(filename, ContentFile(data))
        return True

    def re_generate_thumb(self):
        im = PIL.Image.open(self.content.file.path)
        self.generate_thumb(im, self.thumbnail, THUMBNAIL_PARAMETERS)

    def save(self, *args, **kwargs):
        if self.content.file is not None and \
          (self.width is None or self.height is None):
            try:
                im = PIL.Image.open(self.content.file.path)
                (self.width, self.height) = im.size
            except IOError:
                self.content.status = "INVALID"
                self.content.save()
                return
            self.generate_thumb(im, self.thumbnail, THUMBNAIL_PARAMETERS)
        info = get_imageinfo(self.content.file.path)
        #print type(info)
        #print info # NOTE: this print may raise exception below with some images !?!
        # Exception Value: %X format: a number is required, not NoneType
        # Set lat and lon if they exist in info and NOT yet in content
        if 'lat' in info and info['lat'] and self.content.point is None:
            self.content.point = Point(info['lon'], info['lat'])
        if 'timestamp' in info and self.content.filetime is None:
            self.content.filetime = time.strftime("%Y-%m-%d %H:%M:%S", info['timestamp'])
        if 'title' in info and self.content.title is None:
            self.content.title = info['title']
        if 'caption' in info and self.content.caption is None:
            self.content.caption = info['caption']
        if 'keywords' in info and self.content.keywords is None:
            self.content.keywords = info['keywords']
        # TODO: author and other keys, see filetools.get_imageinfo and iptcinfo.py
        super(Image, self).save(*args, **kwargs) # Call the "real" save() method.
        self.content.status = "PROCESSED"
        self.content.save()

class Video(models.Model):
    content = models.OneToOneField(Content, primary_key=True, editable=False)
    width = models.IntegerField(blank=True, null=True, editable=False)
    height = models.IntegerField(blank=True, null=True, editable=False)
    duration = models.FloatField(blank=True, null=True, editable=False)
    bitrate = models.CharField(max_length=256, blank=True, null=True, editable=False)
    thumbnail = models.ImageField(storage=preview_storage, upload_to=upload_split_by_1000, editable=False)

    def __unicode__(self):
        return u"Video: %s (%dx%dpx, %.2f sec)" % (
                 self.content.originalfilename,
                 self.width, self.height, self.duration)

    def save(self, *args, **kwargs):
        """ Save Video object and in addition:
        - use ffmpeg to extract some information of the video file
        - use ffmpeg to extract and save one thumbnail image from the file
        """
        if self.content.file is not None and \
           (self.width is None or self.height is None):
            info = get_videoinfo(self.content.file.path)
            if 'duration' in info: self.duration = info['duration']
            if 'bitrate' in info: self.bitrate = info['bitrate']
            if 'width' in info: self.width = info['width']
            if 'height' in info: self.height = info['height']
            # Create temporary file for thumbnail
            tmp_file, tmp_name = tempfile.mkstemp()
            if do_video_thumbnail(self.content.file.path, tmp_name):
                filename = u"%s.jpg" % (self.content.uid)
                f = open(tmp_name, "rb")
                self.thumbnail.save(filename, ContentFile(f.read()))
                f.close()
            os.unlink(tmp_name)
        super(Video, self).save(*args, **kwargs) # Call the "real" save() method.
        self.content.status = "PROCESSED"
        self.content.save()

class Audio(models.Model):
    content = models.OneToOneField(Content, primary_key=True)
    duration = models.FloatField(blank=True, null=True)
    def __unicode__(self):
        return u"Audio: %s (%.2f sec)" % (
                 self.content.originalfilename, self.duration)

class Uploadinfo(models.Model):
    """
    All possible information of the client who uploaded the Content file.
    """
    content = models.OneToOneField(Content, primary_key=True, editable=False)
    sessionid = models.CharField(max_length=200, blank=True, null=True, editable=False)
    ip = models.IPAddressField(blank=True, null=True, editable=False)
    useragent = models.CharField(max_length=500, blank=True, null=True, editable=False)
    info = models.TextField(blank=True, null=True, editable=True)
