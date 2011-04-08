'''
Created on Nov 8, 2010

@author: karmel
'''
from django.contrib import admin
from django.template.defaultfilters import urlencode
from glasslab.atlasviewer.utilities.models import SavedQuery


class SavedQueryAdmin(admin.ModelAdmin):
    list_display    = ('id','topic', 'name', 'query_link','stored_link')
    list_filter     = ('topic',)
    ordering        = ('-modified','topic','name')
    
    save_as = True
    
    def query_link(self, obj):
        return '<a href="/transcript/custom_query_redirect/%d" target="_blank">Results</a>' % obj.id
    query_link.short_description = 'Query Results' 
    query_link.allow_tags = True 
    
    def stored_link(self, obj):
        if obj.stored_results:
            return '<a href="/transcript/stored_results/%d" target="_blank">Stored</a>' % obj.id
        else: return ''
    stored_link.short_description = 'Stored Results' 
    stored_link.allow_tags = True 

admin.site.register(SavedQuery, SavedQueryAdmin)
