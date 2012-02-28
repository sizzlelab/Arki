# -*- coding: utf-8 -*-

#from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _
#from django.utils.encoding import smart_unicode, force_unicode
from models import Egg


class UploadForm(forms.Form):
    """Simple upload form."""
    file = forms.FileField(label=_(u'File'), required=False,
                           help_text=_(u"Select a file from your computer"),
                           error_messages={'required': _(u'Select a file from your computer, please!')})

class MessageForm(forms.Form):
    """Simple message (text Egg) form."""
    message = forms.CharField(label=_(u'Message'), required=True)

class EggForm(forms.ModelForm):

    class Meta:
        model = Egg
        fields = ['id', 'caption']
        widgets = {
            #'datalogger': forms.HiddenInput(),
            'uid': forms.HiddenInput(),
            'caption': forms.Textarea(attrs={'cols': 80, 'rows': 3}),
        }

class CommentForm(forms.Form):
    """Simple comment form."""
    egg_uid = forms.CharField(widget=forms.HiddenInput(), required=True)
    comment = forms.CharField(label=_(u'Comment'), required=True)
