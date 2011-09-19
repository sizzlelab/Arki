# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django import forms

MAP_ACTIONS = (
    ('new_spot', _(u'New Spot')),
    ('new_area', _(u'New Area')),
    ('search', _(u'Search')),
)

class MapForm(forms.Form):
    clickaction = forms.CharField(max_length=100, required=False,
                                  widget=forms.Select(choices=MAP_ACTIONS))
    #class Meta:
    #    model = Post
    #    #fields = ('latitude', 'longitude')
    #    exclude = ('point', 'ip', 'useragent', )
