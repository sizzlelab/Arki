# -*- coding: utf-8 -*-

import sys
if __name__=='__main__':
    sys.path.append("..")
import os
import re
import time
import subprocess
import tempfile
import PIL.Image
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import EXIF
from iptcinfo import IPTCInfo


def guess_encoding(str):
    """
    Try to guess is the str utf8, mac-roman or latin-1 encoded.
    http://en.wikipedia.org/wiki/Mac_OS_Roman
    http://en.wikipedia.org/wiki/Latin1
    Code values 00–1F, 7F–9F are not assigned to characters by ISO/IEC 8859-1.
    http://stackoverflow.com/questions/4198804/how-to-reliably-guess-the-encoding-between-macroman-cp1252-latin1-utf-8-and-a
    """
    try:
         unicode(str, 'utf8')
         return "utf8"
    except UnicodeDecodeError:
        if re.compile(r'[\x00–\x1f\x7f-\x9f]').findall(str):
            return "mac-roman"
        else:
            return "latin-1"

def get_mimetype(filepath):
    """
    Return mimetype of given file.
    This uses `file` command found in most unix/linux systems.
    TODO: use python-magic instead for better portability
    >>> magic = magic.open(magic.MAGIC_MIME)
    >>> magic.load()
    >>> magic.file("test.jpg")
    'image/jpeg'
    File for windows:
    http://gnuwin32.sourceforge.net/packages/file.htm
    """
    file_cmd = ['file', '--mime-type', '--brief', '%s' % filepath]
    # FIXME: this doesn't check if executable "file" exist at all
    # TODO: think what to do if this fails
    mime = subprocess.Popen(file_cmd,
                            stdout=subprocess.PIPE).communicate()[0].strip()
    # TODO: REMOVE OLD WAY
    #file_cmd = 'file --mime-type --brief "%s"' % filepath
    #mime = os.popen(file_cmd).read().strip()
    # TODO: it could be a good idea to compare file's and mimetypes' output here?
    return mime

def get_videoinfo(filepath):
    """
    Return duration, bitrate and size of given video file in a dictionary.
    All values are parsed from ffmpeg's output, which looks like
    something like this::

    Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'test.mp4':
      Duration: 00:00:07.27, start: 0.000000, bitrate: 2662 kb/s
        Stream #0.0(und): Video: mpeg4, yuv420p, 640x480 [PAR 1:1 DAR 4:3], 100 tbr, 3k tbn, 100 tbc
        Stream #0.1(und): Audio: aac, 48000 Hz, mono, s16

    Ffmpeg for windows:
    http://sourceforge.net/projects/mplayer-win32/files/
    """
    info = {"duration" : None,
            "bitrate" : None,
            "width" : None,
            "height" : None,
            }
    # FIXME: this doesn't check if executable "ffmpeg" exist at all
    #ffmpeg_cmd = 'ffmpeg -i "%s" 2>&1' % filepath
    #out = os.popen(ffmpeg_cmd).read().strip()
    ffmpeg_cmd = ['ffmpeg', '-i', '%s' % filepath]
    p = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    out = p.stdout.read()
    dt = re.compile("Duration: (\d\d):(\d\d):(\d\d\.\d\d)").findall(out)
    if len(dt) > 0:
        #print dt
        info["duration"] = int(dt[0][0])*60*60 + int(dt[0][1])*60 + float(dt[0][2])
    bt = re.compile("bitrate: (\d+ .*)").findall(out)
    if len(bt) > 0:
        info["bitrate"] = bt[0]
    st = re.compile("Video.* (\d+)x(\d+)").findall(out)
    if len(st) > 0:
        info["width"] = int(st[0][0])
        info["height"] = int(st[0][1])
    return info

# https://gist.github.com/983821

def get_exif_data(image):
    """
    Return a dictionary from the exif data of an PIL Image item.
    Also converts the GPS Tags.
    """
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]
                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
    except AttributeError: # This was missing from original code
        pass
    return exif_data

def _convert_to_degrees(value):
    """
    Helper function to convert the GPS coordinates
    stored in the EXIF to degrees in float format.
    """
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(exif_data):
    """
    Returns the latitude and longitude, if available,
    from the provided exif_data (obtained through get_exif_data above).
    """
    lat = None
    lon = None

    if 'GPSInfo' in exif_data:
        gps_info = exif_data['GPSInfo']
        gps_latitude = gps_info.get('GPSLatitude')
        gps_latitude_ref = gps_info.get('GPSLatitudeRef')
        gps_longitude = gps_info.get('GPSLongitude')
        gps_longitude_ref = gps_info.get('GPSLongitudeRef')
        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat = -lat
            lon = _convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon = -lon
    return lat, lon


def get_imageinfo(filepath):
    """
    Return EXIF and IPTC information found from image file in a dictionary.
    Uses EXIF.py, PIL.Image and iptcinfo.
    NOTE: PIL can read EXIF tags including GPS tags also.
    """
    info = {}
    file = open(filepath, "rb")
    exif = EXIF.process_file(file, stop_tag="UNDEF", details=True, strict=False, debug=False)
    file.close()
    if exif:
        info['exif'] = exif
    # EXIF.py can't parse iPhoto exported
    #if 'GPS GPSLatitude' in exif and \
    #   'GPS GPSLongitude' in exif:
    #    d,m,s = [float(x.num/x.den) for x in exif['GPS GPSLatitude'].values]
    #    info['lat'] = d + m/60.0 + s/60.0/60
    #    d,m,s = [float(x.num/x.den) for x in exif['GPS GPSLongitude'].values]
    #    info['lon'] = d + m/60.0 + s/60.0/60
    #    if str(exif['GPS GPSLatitudeRef']) != 'N':
    #        info['lat'] = -info['lat']
    #    if str(exif['GPS GPSLongitudeRef']) != 'E':
    #        info['lon'] = -info['lon']
    #    #print exif['GPS GPSLongitudeRef'], exif['GPS GPSLatitudeRef']
    #if 'EXIF DateTimeOriginal' in exif:
    #    #print exif['EXIF DateTimeOriginal'], type(exif['EXIF DateTimeOriginal'])
    #    exiftime = str(exif['EXIF DateTimeOriginal'])
    #    try:
    #        info['timestamp'] = time.strptime(exiftime, '%Y:%m:%d %H:%M:%S')
    #    except:
    #        #print exiftime
    #        pass

    im = Image.open(filepath)
    exif_data = get_exif_data(im)
    #print exif_data
    info['lat'], info['lon'] = get_lat_lon(exif_data)
    if 'DateTimeOriginal' in exif_data:
        try:
            info['timestamp'] = time.strptime(exif_data['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
        except:
            #print exiftime
            pass

    iptc = IPTCInfo(filepath, force=True)
    # TODO: extract more tags from iptc (copyright, author etc)
    #iptc2info_map = {
    #    'caption/abstract': 'caption',
    #    'object name': 'title',
    #    'keywords': 'keywords',
    #}
    if iptc:
        info['iptc'] = iptc
        if iptc.data['caption/abstract']:
            info['caption'] = iptc.data['caption/abstract']
        if iptc.data['object name']:
            info['title'] = iptc.data['object name']
        if iptc.data['keywords']:
            info['keywords'] = u', '.join(iptc.data['keywords'])
        # Convert all str values to unicode
        for key in info:
            #print key, type(key)
            if isinstance(info[key], str):
                info[key] = unicode(info[key], guess_encoding(info[key]))
                #print info[key], type(info[key])
    return info

def do_video_thumbnail(src, target):
    """
    Create a thumbnail from video file 'src' and save it to 'target'.
    Return True if subprocess was called with error code 0.
    TODO: make -ss configurable, now it is hardcoded 5 seconds.

    subprocess.check_call(
    ['ffmpeg', '-ss', '1', '-i', 'test_content/05012009044.mp4', '-vframes', '1', '-f', 'mjpeg', '-s', '320x240', 'test-1.jpg'])
    ffmpeg -ss 1 -i test_content/05012009044.mp4 -vframes 1 -f mjpeg -s 320x240 test-1.jpg
    ffmpeg -ss 2 -i test_content/05012009044.mp4 -vframes 1 -f mjpeg -s 320x240 test-2.jpg
    ffmpeg -ss 3 -i test_content/05012009044.mp4 -vframes 1 -f mjpeg -s 320x240 test-3.jpg
    """
    try:
        subprocess.check_call([
            'ffmpeg', '-y', '-ss', '5', '-i', src,
            '-vframes', '1', '-f', 'mjpeg', target
            ])
        return True
    except subprocess.CalledProcessError:
        # TODO: log file and error here.
        return False

# Not implemented
def convert_video(src, target):
    """
    TODO: finish this
    ffmpeg -i test.mp4 -r 24 -s 320x240 -y -f flv -ar 11025 -ab 64 -ac 1 test.flv
    """
    pass

# Not in use
def image_magick_resize(src, target, width, height):
    subprocess.check_call(['convert', src,
                           '-quality', '80',
                           '-geometry','%dx%d' % (width, height), target])
    # ffmpeg -i 000000037-32b9.mp4 -s 160x120  -vframes 1 -f mjpeg preview.jpg
    pass

def create_thumbnail(filepath, t):
        try:
            im = PIL.Image.open(filepath)
        except IOError: # Image file is corrupted
            print "ERROR in image file:", self.content.id, self.content.file
            return False
        if im.mode not in ('L', 'RGB'):
            im = im.convert('RGB')
        size = (t[0], t[1])
        rotatemap = {
            90: PIL.Image.ROTATE_270,
           180: PIL.Image.ROTATE_180,
           270: PIL.Image.ROTATE_90,
        }
        if t[4] != 0:
            im = im.transpose(rotatemap[t[4]])
        im.thumbnail(size, PIL.Image.ANTIALIAS)
        # TODO: use imagemagick and convert
        # Save resized image to a temporary file
        # NOTE: the size will be increased if original is smaller than size
        tmp = tempfile.NamedTemporaryFile() # FIXME: use StringIO
        im.save(tmp, "jpeg", quality=t[3])
        tmp.seek(0)
        return tmp


if __name__=='__main__':
    info = get_imageinfo(sys.argv[1])
    if 'exif' in info and 'JPEGThumbnail' in info['exif']:
        del info['exif']['JPEGThumbnail']
    #print info['exif']
    print info['exif'].keys()
     # w, h, format, quality, rotate
    THUMBNAIL_PARAMETERS = (200, 200, 'JPEG', 80, 0)
    thumb = create_thumbnail(sys.argv[1], THUMBNAIL_PARAMETERS)
    thumb.close()
    print thumb.name
