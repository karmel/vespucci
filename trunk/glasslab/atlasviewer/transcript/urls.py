'''
Created on Nov 16, 2010

@author: karmel
'''
from django.conf.urls.defaults import patterns
urlpatterns = patterns('glasslab.atlasviewer.transcript.views',
    
    (r'^custom_query_export', 'custom_query_export'),
    (r'^custom_query', 'custom_query'),    
)
