API
===

The MestaDB ReST API accepts HTTP POST requests
(also GET requests in debug mode)
and there is always one mandatory parameter, "operation", in request.

Response data is returned in JSON format except when response is
e.g. an image or a video file.

Requests
--------

After the MestaDB is up and running you can try how API works with curl, first log in::

    curl -i -c cookies.txt -d "operation=login&username=testuser&password=testpassword" http://127.0.0.1:8000/api/

    HTTP/1.0 200 OK
    Date: Wed, 28 Sep 2011 05:56:51 GMT
    Server: WSGIServer/0.1 Python/2.6.6
    Vary: Accept-Language, Cookie
    Content-Length: 95
    Content-Type: application/json
    Content-Language: en
    Set-Cookie:  sessionid=f187d0a657ca46ad0e045ab72be31347; expires=Wed, 12-Oct-2011 05:56:51 GMT; Max-Age=1209600; Path=/

    {
     "status": "ok",
     "sessionid": "f187d0a657ca46ad0e045ab72be31347",
     "message": "Login OK"
    }

Then check if the session is valid::

    curl -i -b cookies.txt -d "operation=sessioninfo" http://127.0.0.1:8000/api/

    HTTP/1.0 200 OK
    Date: Wed, 28 Sep 2011 06:54:04 GMT
    Server: WSGIServer/0.1 Python/2.6.6
    Vary: Accept-Language, Cookie
    Content-Length: 217
    Content-Type: application/json
    Content-Language: en

    {
     "username": "testuser",
     "status": "ok",
     "sessionid": "895ed908a4fdddf503f599b42d615259",
     "is_staff": true,
     "message": "Authenticated session",
     "expiry_date": "2011-10-12T09:54:04",
     "expiry_age": 1209600
    }

If client accepts zlib compression client may imply it by sending HTTP header::

    Accept-Encoding: deflate

For example::

    curl -i -b cookies.txt -c cookies.txt -H "Accept-Encoding: deflate" -d "operation=sessioninfo" http://127.0.0.1:8000/api/

    HTTP/1.0 200 OK
    Date: Wed, 28 Sep 2011 06:59:28 GMT
    Server: WSGIServer/0.1 Python/2.6.6
    Vary: Accept-Language, Cookie
    Content-Length: 159
    Content-Type: application/json
    Content-Language: en
    Content-Encoding: deflate

    x?U???0E??????IlJ?;??}??D???<@????q7?{?O%d?&;?셴??d?A^???B??N8F?O?ءa
    B?l??8:?xi4??h???ǡx?+?2?l,{??r?????&&???%??>?*??ԠT??V??u??ۄJ????...

Responses
---------

Response contains always two mandatory keys:
``status``, which can be ``ok`` or ``error`` and an informal ``message``,
which may be empty.

JSON responses have HTTP header::

    Content-Type: application/json

If client sent ``Accept-Encoding: deflate`` header,
the MestaDB response contains HTTP header::

    Content-Encoding: deflate

and the content is zlib compressed.

Operations
----------
All available remote operations and parameters are listed below.

=================== =============== =======================================
Operation           Parameters      Returns (in addition to status+message)
=================== =============== =======================================
login               username=string
                    password=string
logout      t       None
content_post        file=fileobject file's: uid, md5, sha1
                    caption etc.
content_update      caption etc.
=================== =============== =======================================


curl -v -b cookies.txt -d "operation=spot_nearby_get&lat=60.27&lon=24.98" http://127.0.0.1:8000/api/

curl  -v -b cookies.txt -F "file=@content/testfiles/lounas-nakki-nuuksiossa.jpg" -F "author=testuser" http://127.0.0.1:8000/api/

TODO: fix automodule/autofunction

Modules
-------

:mod:`mestadb.api.views`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: mestadb.api.views

:mod:`mestadb.api.handler`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: mestadb.api.handler

:mod:`mestadb.api.authentication`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: mestadb.api.authentication
.. autofunction:: mestadb.api.authentication.login
.. autofunction:: mestadb.api.authentication.logout
.. autofunction:: mestadb.api.authentication.sessioninfo

:Author: Aapo Rista
