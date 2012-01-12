# -*- coding: utf-8 -*-

from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode, force_unicode



class UploadForm(forms.Form):
    """Simple upload form."""
    file = forms.FileField(label=_(u'File'), required=False,
                           help_text=_(u"Select a file from your computer"),
                           error_messages={'required': _(u'Select a file from your computer, please!')})

