# -*- coding: utf-8 -*-
# $Id$
"""
Core's admin definitions.

You can override these in your own application's admin.py, just do this:

from models import Content
admin.site.unregister(Content)
class ContentAdmin(admin.ModelAdmin):
    # your model admin definitions here

admin.site.register(Content, ContentAdmin)
"""

from django.contrib import admin
from models import Egg

class EggAdmin(admin.ModelAdmin):
    search_fields = ('title', 'caption', 'author')
    list_display = ('title', 'caption', 'author', 'created', 'updated')
    ordering = ('title',)

admin.site.register(Egg, EggAdmin)
