# -*- coding: utf-8 -*-

import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import widgets
from django.conf import settings

class LoginForm(forms.Form):
    username = forms.CharField(max_length=75, label=_(u'Username'), required=True)
    password = forms.CharField(max_length=75, label=_(u'Password'), widget=forms.PasswordInput, required=True)
