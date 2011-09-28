# -*- coding: utf-8 -*-

from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode, force_unicode

from filehandler import handle_uploaded_file
from models import Content


class UploadForm(forms.Form):
    """Simple upload form."""
    file = forms.FileField(label=_(u'File'), help_text=_(u"Select a file from your computer"),
                           error_messages={'required': _(u'Select a file from your computer, please!')})


class ContentModelForm(forms.ModelForm):
    """Plain edit form for all content files."""
    latlon = forms.CharField(label=_(u'Coordinates (lat,lon)'), required=False)
    class Meta:
        model = Content
        fields = ['title', 'caption', 'author']
        fields += ['keywords', 'place']
        fields += ['privacy', 'opens', 'expires']
        fields += ['latlon']

    def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data.get('latlon'):
            try: # Check that lat,lon is comma separated pair of floats
                lat, lon = [float(x) for x in cleaned_data.get('latlon').split(',')]
            except:
                raise forms.ValidationError(_(u'Coordinates must be in format "dd.dddd,dd.dddd".'))
        # Always return the full collection of cleaned data.
        return cleaned_data


class SearchForm(forms.Form):
    q = forms.CharField(max_length=160, label=_(u'Quick search'),
                        help_text=_(u"Write at least 2 characters."))
