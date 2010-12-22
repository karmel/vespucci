'''
Created on Nov 8, 2010

@author: karmel
'''
from django.contrib import admin
from django.template.defaultfilters import urlencode
from glasslab.atlasviewer.utilities.models import SavedQuery


class SavedQueryAdmin(admin.ModelAdmin):
    list_display    = ('id','topic', 'name', 'query_link')
    list_filter     = ('topic',)
    ordering        = ('-modified','topic','name')
    
    save_as = True
    
    def query_link(self, obj):
        return '<a href="/transcript/custom_query?query=%s" target="_blank">Results</a>' % urlencode(obj.query)
    query_link.short_description = 'Query Results' 
    query_link.allow_tags = True 

admin.site.register(SavedQuery, SavedQueryAdmin)
