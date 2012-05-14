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
from models import Content
#from models import Set
#from models import Content, Category, Set, Text
#from multilingual.admin import MultilingualModelAdmin

#import multilingual

class ContentAdmin(admin.ModelAdmin):
    search_fields = ('title', 'caption', 'mimetype', 'caption')
    list_display = ('title',  'caption', 'mimetype', 'filesize', 'created', 'updated')
    ordering = ('title',)

admin.site.register(Content, ContentAdmin)


#class CategoryAdmin(MultilingualModelAdmin):
#    pass
    #list_display = ('id', 'name',)
    #search_fields = ('name',)
    #ordering = ('name',)

#admin.site.register(Category, CategoryAdmin)

#class TextAdmin(admin.ModelAdmin):
#class TextAdmin(MultilingualModelAdmin):
#    search_fields = ('realm', 'key', 'text')
#    list_display = ('realm', 'key', 'text')
#    ordering = ('realm', 'key',)

#admin.site.register(Text, TextAdmin)


#class SetAdmin(admin.ModelAdmin):
#    search_fields = ('title', )
#    list_display = ('title', 'uid',)
#    ordering = ('title',)
#
#admin.site.register(Set, SetAdmin)
