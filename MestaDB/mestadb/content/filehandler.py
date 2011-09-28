# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _

import time
import tempfile

def handle_uploaded_file(request):
    """
    Save all files found in request.FILES to filesystem.
    """
    for inputfile in request.FILES:
        tmp_file, tmp_name = tempfile.mkstemp()
        filedata = request.FILES[inputfile]
        original_filename = filedata.name
        destination = open(tmp_name, 'wb')
        for chunk in filedata.chunks():
            destination.write(chunk)
        destination.close()
        yield inputfile, tmp_name
