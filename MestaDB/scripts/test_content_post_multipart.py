# -*- coding: utf-8 -*-

import sys
import os
import httplib
import random
import string

import hmac
import hashlib


CRLF = '\r\n'
BUFFER_SIZE = 32*1024


class Handler:
    """Base class for all multipart handlers."""

    def __init__(self):
        self.length = 0
        self.data = ''

    def set_data(self, data):
        if isinstance(data, list):
            data.append('') # add CRLF to the end
            self.data = str(CRLF.join(data))
            while len(data) > 0: # empty the list L
                data.pop()
        else:
            self.data = data


class ContentLengthHandler(Handler):
    """Count the length of the encoded POST."""

    def __init__(self, hmacs):
        Handler.__init__(self)
        self.hmacs = hmacs

    def write(self, data):
        self.set_data(data)
        self.length += len(self.data)
        for digest_maker in self.hmacs:
            digest_maker.update(self.data)

    # TODO: implement this (add file size instead of reading file through), because reading 100 MB file twice is now wise
    #def add_file(self, filepath):
    #    self.length += os.stat(filepath)[stat.ST_SIZE]


class HttpHandler(Handler):
    """Write sends the data directly to the HTTP connection (socket)."""

    def __init__(self, conn, total_length):
        Handler.__init__(self)
        self.done = 0
        self.conn = conn
        self.total_length = total_length

    def write(self, data):
        self.set_data(data)
        self.conn.send(self.data)
        self.done += len(self.data)
        #print self.done, self.total_length


class FileHandler(Handler):
    """ Write the data directly to the file for debugging purposes."""

    def __init__(self, fname, total_length):
        Handler.__init__(self)
        self.f = open(fname, 'wb')
        self.done = 0
        self.total_length = total_length

    def write(self, data):
        self.set_data(data)
        self.f.write(self.data)
        self.done += len(self.data)

class HttpPostMultipart:

    def __init__(self, username, secret):
        self.username = username
        self.secret = secret

    def random_boundary(self, length=30):
        alphanum = string.letters + string.digits
        return ''.join([alphanum[random.randint(0,len(alphanum)-1)] for i in xrange(length)])

    def get_content_type(self, filename):
        # TODO: use mimetypes or something here instead of hardcoded value
        return 'application/octet-stream'

    def encode_multipart_formdata(self, boundary, fields, files, handler):
        lines = []
        for (key, value) in fields.iteritems():
            lines.append('--' + boundary)
            lines.append('Content-Disposition: form-data; name="%s"' % key)
            lines.append('')
            lines.append(value)
            handler.write(lines)
        for (key, filename, value) in files:
            lines.append('--' + boundary)
            lines.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            lines.append('Content-Type: %s' % self.get_content_type(filename))
            lines.append('')
            handler.write(lines)
            # If value is open file handle, read the file
            if isinstance(value, file): # FIXME: check that file is really is open!
                value.seek(0)
                buf = value.read(BUFFER_SIZE) # read in BUFFER_SIZE blocks
                while len(buf) > 0:
                    handler.write(buf)
                    buf = value.read(BUFFER_SIZE)
            elif isinstance(value, str):
                if os.path.isfile(value): # If value is a path to an existing file
                    f = open(value, 'rb') # FIXME: THIS MAY FAIL!
                    buf = f.read(BUFFER_SIZE) # read 4k blocks
                    while len(buf) > 0:
                        handler.write(buf)
                        buf = f.read(BUFFER_SIZE)
                    f.close()
                else: # If value is plain string use it as-is
                    lines.append(value)
                    handler.write(lines)
            elif isinstance(value, str) is False:
                raise ValueError("In-memory-file must be str, file obj or filename, not %s!" % (type(value)))
                #sys.exit(1)
        lines.append('--' + boundary + '--')
        handler.write(lines)
        content_type = 'multipart/form-data; boundary=%s' % boundary
        return handler.length, content_type


    def post_multipart(self, host, selector, fields, files, headers={}):
        """
        POST multipart/form-data formatted request to host.
        fields is a dictionary.
        files is a list of 3-item tuples
            (file field name, file's name, open filehandle or filepath or str)
        See also:
        http://www.w3.org/Protocols/rfc1341/7_2_Multipart.html
        """
        boundary = '----------' + self.random_boundary() + '_$'
        sha1_digest_maker = hmac.new(self.secret, '', hashlib.sha1)
        md5_digest_maker = hmac.new(self.secret, '', hashlib.md5)
        content_length, content_type = self.encode_multipart_formdata(boundary, fields, files, handler=ContentLengthHandler([sha1_digest_maker, md5_digest_maker]))
        sha1_digest = sha1_digest_maker.hexdigest()
        md5_digest = md5_digest_maker.hexdigest()
        #print sha1_digest, md5_digest
        hmac_header = 'username=%s;sha1=%s;md5=%s' % (self.username, sha1_digest, md5_digest)
        # Delete inappropriate headers
        for header in headers.keys():
            if header.lower() in ['content-type', 'content-length']:
                del headers['header']
        # Add mandatory headers
        headers.update({
            'Content-Type': content_type,
            'Content-Length': content_length,
            'X-4Dnest-hmac': hmac_header,
        })
        # Create connection object
        h = httplib.HTTPConnection(host)
        # Construct request headers
        h.putrequest('POST', selector)
        for key, val in headers.items():
            h.putheader(key, val)
        h.endheaders()
        # Put POST's payload in the place
        httphandler = HttpHandler(h, content_length)
        content_length, content_type =  self.encode_multipart_formdata(boundary, fields, files, handler=httphandler)
        # Uncomment to DEBUG:
        #filehandler = FileHandler('/tmp/httppost.txt', content_length)
        #self.encode_multipart_formdata(boundary, fields, files, handler=filehandler)
        response = h.getresponse()
        return response

if __name__ == '__main__':
    host = '127.0.0.1:8000'
    selector = '/fourdnest/api/v1/egg/upload/'
    headers = {'Cookie': 'sessionid=7c77f05283b41d74850dee610ddca993'}
    fields = {'title': 'Cool title', 'caption': 'Nice file', 'author': 'Python user'}
    files = []
    #files.append(('file1', 'in-memory-file1.txt', u'Hahhaahhaa, naurattaa\nfuubar\nMites nää ääkköset ja €uro?')) # this should fail
    #files.append(('file1', 'in-memory-file1.txt', u'Hahhaahhaa, naurattaa\nfuubar\nMites nää ääkköset ja €uro?'.encode('utf8')))
    #files.append(('file2', 'in-memory-file2.txt', 'x'*80+'\n'))
    #if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    #    f = open(sys.argv[1], 'rb')
    #    files.append(('file', 'open-filehandle.bin', f))
    #print os.path.basename(sys.argv[1])
    if len(sys.argv) > 1:
        files.append(('file', os.path.basename(sys.argv[1]), sys.argv[1]))
    hpm = HttpPostMultipart('test42', 'random secret string is here')
    response = hpm.post_multipart(host, selector, fields, files, headers)
    print response.read()
    print "STATUS", response.status, response.getheaders()
