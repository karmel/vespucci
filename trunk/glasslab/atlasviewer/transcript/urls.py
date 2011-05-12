'''
Created on Nov 16, 2010

@author: karmel
'''
from django.conf.urls.defaults import patterns
urlpatterns = patterns('glasslab.atlasviewer.transcript.views',
    
    (r'^stored_results/(?P<id>\d+)', 'stored_results'),
    (r'^stored_results_export/(?P<id>\d+)', 'stored_results_export'),
    (r'^restore_query/(?P<id>\d+)', 'restore_query'),
    (r'^custom_query_export', 'custom_query_export'),
    (r'^custom_query_redirect/(?P<id>\d+)', 'custom_query_redirect'),
    (r'^custom_query', 'custom_query'),
    (r'^transcripts_ucsc_track_0', 'transcripts_ucsc_track_0'),
    (r'^transcripts_ucsc_track_1', 'transcripts_ucsc_track_1'),
)
