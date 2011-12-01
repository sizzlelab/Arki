# -*- coding: utf-8 -*-

import sys
import os
import httplib
import random
import string
import datetime
import hmac
import base64
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

    #def __init__(self, fname, total_length):
    def __init__(self, fname):
        Handler.__init__(self)
        self.f = open(fname, 'wb')
        self.done = 0
        #self.total_length = total_length

    def write(self, data):
        self.set_data(data)
        self.f.write(self.data)
        self.done += len(self.data)

class HttpPostMultipart:

    def __init__(self, username, secret):
        self.username = username
        self.secret = secret
        self.request_method = 'POST'

    def random_boundary(self, length=30):
        alphanum = string.letters + string.digits
        return ''.join([alphanum[random.randint(0,len(alphanum)-1)] for i in xrange(length)])

    def get_content_type(self, filename):
        # TODO: use mimetypes or something here instead of hardcoded value
        return 'application/octet-stream'

    def encode_multipart_formdata(self, boundary, fields, files, handler):
        lines = []
        hashes = []
        keys = fields.keys()
        keys.sort() # Put keys to alphabethical order for easier fourdnest_md5 calculation
        for key in keys:
            value = fields[key]
            lines.append('--' + boundary)
            lines.append('Content-Disposition: form-data; name="%s"' % key)
            lines.append('')
            lines.append(value)
            hashes.append(hashlib.md5(value).hexdigest())
            handler.write(lines)
        for (key, filename, value) in files:
            lines.append('--' + boundary)
            lines.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            lines.append('Content-Type: %s' % self.get_content_type(filename))
            lines.append('')
            handler.write(lines)
            digest_maker = hashlib.md5()
            # If value is open file handle, read the file
            if isinstance(value, file): # FIXME: check that file is really is open!
                value.seek(0)
                buf = value.read(BUFFER_SIZE) # read in BUFFER_SIZE blocks
                while len(buf) > 0:
                    handler.write(buf)
                    digest_maker.update(buf)
                    buf = value.read(BUFFER_SIZE)
            elif isinstance(value, str):
                if os.path.isfile(value): # If value is a path to an existing file
                    f = open(value, 'rb') # FIXME: THIS MAY FAIL!
                    buf = f.read(BUFFER_SIZE) # read BUFFER_SIZE blocks
                    #digest_maker.update(buf)
                    while len(buf) > 0:
                        handler.write(buf)
                        digest_maker.update(buf)
                        buf = f.read(BUFFER_SIZE)
                    f.close()
                else: # If value is plain string use it as-is
                    lines.append(value)
                    digest_maker.update(value)
                    handler.write(lines)
            elif isinstance(value, str) is False:
                raise ValueError("In-memory-file must be str, file obj or filename, not %s!" % (type(value)))
                #sys.exit(1)
            # Add extra newline to the end of file field
            handler.write(CRLF)
            #digest_maker.update(CRLF)
        hashes.append(digest_maker.hexdigest())
        print hashes
        #print ''.join(hashes)
        fourdnest_multipart_md5 = hashlib.md5(''.join(hashes)).hexdigest()
        lines.append('--' + boundary + '--')
        handler.write(lines)
        content_type = 'multipart/form-data; boundary=%s' % boundary
        return handler.length, content_type, fourdnest_multipart_md5

    def add_authorization_header(self, headers, content_type, request_uri, content_md5, fourdnest_multipart_md5):
        #hmac_header = 'username=%s;sha1=%s;md5=%s' % (self.username, sha1_digest, md5_digest)
        fourdnest_multipart_md5_b64 = base64.b64encode(fourdnest_multipart_md5)
        message = "\n".join([self.request_method,
                             content_md5,
                             fourdnest_multipart_md5_b64,
                             content_type,
                             headers['Date'],
                             request_uri])
        #print message
        hash = hmac.new(self.secret, message, hashlib.sha1)
        encoded = base64.b64encode(hash.hexdigest())
        hmac_header = '%s:%s' % (self.username, encoded)
        headers.update({
            'Authorization': hmac_header,
            'X-4Dnest-MultipartMD5': fourdnest_multipart_md5_b64,
        })

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

        # Uncomment to DEBUG, this should write multipart data to a file even if there is no server available
        filehandler = FileHandler('/tmp/httppost.txt')
        self.encode_multipart_formdata(boundary, fields, files, handler=filehandler)

        # Calculate md5 hash of the POST body
        md5_digest_maker = hashlib.md5()
        content_length, content_type, fourdnest_multipart_md5 = self.encode_multipart_formdata(boundary, fields, files, handler=ContentLengthHandler([md5_digest_maker]))

        # Delete inappropriate headers
        for header in headers.keys():
            if header.lower() in ['content-type', 'content-length']:
                del headers[header]
        # Add mandatory headers
        tstamp = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        headers.update({
            'Content-Type': content_type,
            'Content-Length': content_length,
            'Date': tstamp,
        })
        #self.add_authorization_header(headers, content_type, selector, md5_digest_maker.hexdigest(), fourdnest_multipart_md5)
        # Use fourdnest_multipart_md5, content_md5 is empty string
        self.add_authorization_header(headers, content_type, selector, '', fourdnest_multipart_md5)
        print "REQUEST:"
        for key, val in headers.items():
            print "%s: %s" % (key, val)

        # Create connection object
        h = httplib.HTTPConnection(host)
        # Construct request headers
        h.putrequest(self.request_method, selector)
        for key, val in headers.items():
            h.putheader(key, val)
        h.endheaders()
        # Put POST's payload in the place
        httphandler = HttpHandler(h, content_length)
        content_length, content_type, fourdnest_multipart_md5 =  self.encode_multipart_formdata(boundary, fields, files, handler=httphandler)
        response = h.getresponse()
        return response

# TODO: add command line options: debug, verbose
if __name__ == '__main__':
    host = '127.0.0.1:8000'

    #host = 'test42.4dnest.org'
    selector = '/fourdnest/api/v1/egg/upload/'
    #headers = {'Cookie': 'sessionid=7c77f05283b41d74850dee610ddca993'}
    headers = {}
    fields = {'title': 'Cool title', 'caption': 'Nice file', 'author': 'Python user'}
    files = []
    #files.append(('file1', 'in-memory-file1.txt', u'Foobarbaz\nfuubar\nMites nää ääkköset ja €uro?')) # this should fail
    #files.append(('file1', 'in-memory-file1.txt', u'Hola carabola\nfuubar\nMites nää ääkköset ja €uro?'.encode('utf8')))
    #files.append(('file2', 'in-memory-file2.txt', 'x'*80+'\n'))
    #if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    #    f = open(sys.argv[1], 'rb')
    #    files.append(('file', 'open-filehandle.bin', f))
    #print os.path.basename(sys.argv[1])
    if len(sys.argv) > 1:
        files.append(('file', os.path.basename(sys.argv[1]), sys.argv[1]))
    print "FIELDS:", fields
    print "FILES:", files
    hpm = HttpPostMultipart('test42', 'secret')
    response = hpm.post_multipart(host, selector, fields, files, headers)
    print response.read()
    print "RESPONSE:"
    print "STATUS:", response.status
    for (key, val) in response.getheaders():
        print "%s: %s" % (key, val)
