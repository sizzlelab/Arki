# -*- coding: utf-8 -*-

import datetime

from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.contrib import auth
from django.contrib import messages
from django.core.urlresolvers import reverse

from forms import LoginForm
from models import LoginAttempt

def _render_to_response(request, template, variables):
    """
    Wrapper for render_to_response() shortcut.
    Puts user, perms and some other common variables available in template.
    """
    if not request.session.get('starttime', False):
        request.session["starttime"] = datetime.datetime.now()
    variables['request'] = request
    host = request.META.get('HTTP_HOST', u'').lower()
    if host.startswith('test42'):
        variables['test'] = u'SANDBOX'
    if host.startswith('127.0.0.1') or host.startswith('mytestapp.org') :
        variables['test'] = u'LOCALHOST'
    return render_to_response(
        template, variables, context_instance=RequestContext(request),
    )

def index(request):
    """Render front page and handle login."""
    if request.method == 'POST': # If the login form has been submitted...
        loginform = LoginForm(request.POST)
        loginattempt = LoginAttempt()
        loginattempt.username = request.POST.get('username')
        redirect = HttpResponseRedirect(reverse('defaultapp_index'))
        if loginform.is_valid():
            username = loginform.cleaned_data.get('username')
            password = loginform.cleaned_data.get('password')
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    auth.login(request, user) # Login and redirect to a success page.
                    loginattempt.user = user
                    loginattempt.result = 'LOGIN_SUCCESSFUL'
                    if request.POST.get('next'):
                        redirect = HttpResponseRedirect(request.POST.get('next'))
                    else:
                        redirect = HttpResponseRedirect(reverse('defaultapp_index'))
                else:
                    # Return a 'disabled account' error message
                    msg = _(u'Login failed - account is disabled.')
                    messages.error(request, msg)
                    loginattempt.result = 'USER_NOT_ACTIVE'

            else:
                # Return an 'invalid login' error message.
                msg = _(u'Login failed - invalid username or password.')
                messages.error(request, msg)
                loginattempt.result = 'USERNAME_PASSWORD_MISMATCH'
        else:
            msg = _(u'Login failed - username and/or password not provided.')
            messages.error(request, msg)
            loginattempt.result = 'USERNAME_OR_PASSWORD_NOT_PROVIDED'
            redirect = HttpResponseRedirect(reverse('defaultapp_index'))
        loginattempt.set_data(request)
        loginattempt.save()
        return redirect

    return _render_to_response(request, 'defaultapp_index.html', {
        'loginform': LoginForm(),
        'visible_apps': settings.VISIBLE_APPS,
    })

def logout(request):
    loginattempts = LoginAttempt.objects.filter(session_key__exact=request.session.session_key).order_by('-id')
    if loginattempts:
        loginattempts[0].logouttime = datetime.datetime.now()
        loginattempts[0].save()
    auth.logout(request)
    return HttpResponseRedirect(reverse('defaultapp_index'))
