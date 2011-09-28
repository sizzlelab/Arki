# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

class LoginAttempt(models.Model):
    """
    Login attempts (successful and failed) and other information about user.
    """
    RESULT_CHOICES = (
        ('LOGIN_SUCCESSFUL', _(u'Login successful')),
        ('USERNAME_NOT_FOUND', _(u'Username does not exist')),
        ('USERNAME_PASSWORD_MISMATCH', _(u'Username and password did not match')),
        ('USER_NOT_ACTIVE', _(u'User account is not active')),
        ('USERNAME_OR_PASSWORD_NOT_PROVIDED', _(u'Username or password was missing')),
    )
    username = models.CharField(max_length=128, verbose_name=_('Username'))
    user = models.ForeignKey(User, null=True, related_name='loginattemps', verbose_name=_('User'))
    logintime = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('Login time'))
    logouttime = models.DateTimeField(null=True, editable=False, verbose_name=_('Logout time'))
    result = models.CharField(max_length=64, choices=RESULT_CHOICES, verbose_name=_('Login attempt result'))
    session_key = models.CharField(max_length=128)
    ip = models.IPAddressField()
    useragent = models.CharField(max_length=1000)

    def __unicode__(self):
        return u'%s, %s, %s' % (self.username, self.logintime, self.session_key)

    def set_data(self, request):
        """Shortcut to save request data."""
        self.username = request.POST.get('username')
        self.session_key = request.session.session_key
        self.ip = request.META.get('REMOTE_ADDR', None)
        self.useragent = force_unicode(request.META.get('HTTP_USER_AGENT', u""))[:500]
