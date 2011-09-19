# -*- coding: utf-8 -*-

from django.conf import settings

from django.contrib.auth.models import User
#from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.template import Context
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode, force_unicode

from django.db.models import Avg, Max, Min, Count, Sum

from django.contrib.auth.models import User

#import models
from models import Realm, Spot, Area
import forms

import os
import datetime
import json

def _render_to_response(request, template, variables):
    """
    Wrapper for render_to_response() shortcut.
    Puts user, perms and some other common variables available in template.
    """
    if not request.session.get('starttime', False):
        request.session["starttime"] = datetime.datetime.now()
    variables['request'] = request
    return render_to_response(template, variables,
                              context_instance=RequestContext(request),
                             )

# @login_required
def index(request):
    """
    Renders the front page of Place.
    """
    realms = Realm.objects.all()
    return _render_to_response(request, 'place_base.html', {
        'realms': realms,
        'mapform': forms.MapForm(),
    })
