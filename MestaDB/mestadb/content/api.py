"""
:mod:`content.api` Content's models related functions.

operations defined here:

* content_post(caption, sender, tags) -> id (uid)

* content_put(caption, tags, visibility) ->

* get_files_newest() -> filelist[{
"time":"2010-03-14T19:20:02", "id":"37448", "lat":60.917, "lon":26.2433333,
"sender":"Mika","title":"Jimmy & Player's Bar","size":"6716",
"type":"image\/jpeg", "image_base64":"JAHSGDALJSHGDALJHDSGJLDGLA..."}, {}]

* get_file(id) -> file-object

* get_messages() -> "chatmessages":[
{"sender":"Eeva","text":"[PyS60Gps] Hiiht\u00e4m\u00e4ss\u00e4","id":"75020",
 "sendtime":"2010-03-14T17:16:48"},{...}]

Thoughts:

? content_put(uid, fileobj, ...) creates new a Content with uid or replaces existing content with the same uid
- content_post(fileobj, ...) creates a new Content
- content_update(uid, ...) updates Content's metadata with ...
- content_delete(uid, ...) deletes Content with uid
- content_get(uid) gets content and metadata
- content_search(...) finds content with filter parameters ... (lat/lon/distance, user_id, keywords, )

"""

import json # import simplejson if using python 2.5
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode, force_unicode
from django.contrib.gis.geos import Point

from content.models import *
from filehandler import handle_uploaded_file
from apijson.handler import login_required

@login_required
def content_post(request):
    """
    Create new Content(s) from file(s) found in posted multipart-form.
    Request must be multipart/form-data encoded and must have
    "Content-Type: multipart/form-data;" header present.
    Return a list of saved files containing uids, md5 and sha1 hash sums
    filesize and mimetype.
    """

    saved_files = []
    data = {}
    #print str(request.FILES)
    for filefield_name, filename in handle_uploaded_file(request):
        P = request.POST
        c = Content(user = request.user,
                    author = P.get('sender', request.user.username),
                    caption = P.get('caption'),
                    keywords = P.get('tags'),
                    privacy = P.get('privacy', 'PRIVATE'),
        )
        originalname = str(request.FILES[filefield_name])
        c.set_file(originalname, filename)
        c.get_type_instance()
        c.save()
        saved_files.append({
                'uid': c.uid,
                'filesize': c.filesize,
                'md5': c.md5,
                'sha1': c.sha1,
                'mimetype': c.mimetype,
        })
    if len(saved_files) > 0:
        message = _(u'Saved %d file(s)' % len(saved_files))
        data = {
            'files': saved_files,
            'id': saved_files[0]['uid'], # FIXME: remove backwards compatibility (pys60gps requires one id here)
        }
        return True, data, message
    else:
        message = _(u'File not found in post')
        return False, data, message

@login_required
def content_update(request):
    P = request.POST
    uid = P.get('uid', '')
    data = {}
    if uid == '': # backwards compatibility
        uid = P.get('id', '')
    try:
        c = Content.objects.get(uid=uid)
    except Content.DoesNotExist, e:
        message = _(u'Content uid=%s not found' % uid)
        return False, data, message
    if c.user != request.user: # Require ownership
        message = _(u'You are not owner of Content uid=%s' % uid)
        return False, data, message
    if P.get('caption') is not None:
        c.caption = P.get('caption')
    if P.get('place') is not None:
        c.place = P.get('place')
    if P.get('author') is not None:
        c.author = P.get('author')
    if P.get('keywords') is not None:
        c.keywords = P.get('keywords')
    elif P.get('tags') is not None: # backwards compatibility
        c.keywords = P.get('tags')
    privacy = P.get('privacy') or P.get('visibility') # Backwards compatibility, TODO: remove in later version of API
    c.privacy = privacy
    c.save()
    message = _(u'Changes saved')
    return True, data, message

@login_required
def content_not_implemented_yet(request):
    """FIXME: not implemented"""
    # TODO: log all calls of this function
    return False, {}, _(u'Not implemented yet, sorry!')


POST_CALLS = {
    'content_post': content_post,
    'content_update': content_update,
    'content_delete': content_not_implemented_yet,
    'content_get': content_not_implemented_yet,
    'content_search': content_not_implemented_yet,
    # DEPRECATED
    'send_file': content_post, # Deprecated, backwards compatibility
    'update_file': content_update, # Deprecated, backwards compatibility
}
