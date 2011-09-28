# -*- coding: utf-8 -*-
"""
:mod:`mestadb.api.authentication` wraps Django's
authenticate(), login() and logout() functions.

For command line testing::

    curl -v -c sessionid.cookie -d operation=login -d username=existing_username -d password=real_password http://127.0.0.1:8000/api/
    curl -v -b sessionid.cookie -d operation=sessioninfo http://127.0.0.1:8000/api/
    curl -v -b sessionid.cookie -d operation=logout http://127.0.0.1:8000/api/

"""

from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout

from django.utils.translation import ugettext as _

def login(request):
    """
    Check (lowercased) usename and password and do login if they matched.
    Only POST request is allowed.
    Return status and message in a dictionary.
    """
    success = False
    data = {}
    message = u''
    if request.method != 'POST':
        message =  _("Only POST method is allowed when you log in.")
        return False, None, message

    sessionid = None
    if "username" in request.POST and "password" in request.POST:
        user = django_authenticate(username=request.POST["username"].lower(),
                                   password=request.POST["password"])
    else:
        message =  _("Missing username and/or password parameter.")
        return False, None, message
    if user is not None:
        if user.is_active:
            success = True
            message =  _("Login OK")
            # This puts sessionid cookie into the response headers:
            django_login(request, user)
            sessionid = request.session.session_key
        else:
            message =  _("Your account has been disabled!")
    else:
        message =  _("Your username and password did not match.")
    data = {"sessionid": sessionid}
    return success, data, message

def logout(request):
    """Logout user and terminate session. Returns always OK."""
    django_logout(request)
    data = {}
    message = _("Logout OK")
    return True, data, message

def sessioninfo(request):
    """Return some session data."""
    if request.user.is_authenticated():
        username = request.user.username
        message = _(u"Authenticated session")
    else:
        username = None
        message = _(u"Anonymous session")

    data = {"sessionid" : request.session.session_key,
            "username" : username,
            "is_staff" : request.user.is_staff,
            "expiry_age" : request.session.get_expiry_age(),
            "expiry_date" : request.session.get_expiry_date().strftime("%Y-%m-%dT%H:%M:%S"),
            }
    return True, data, message


POST_CALLS = {
    "login" : login,
    "logout" : logout,
    "sessioninfo" : sessioninfo,
}
