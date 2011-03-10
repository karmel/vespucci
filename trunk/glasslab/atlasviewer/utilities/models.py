'''
Created on Dec 9, 2010

@author: karmel
'''
from django.db import models

class SavedQuery(models.Model):
    '''
    Convenience model for saving queries, with links to results.
    '''
    topic   = models.CharField(max_length=255, default='General')
    name    = models.CharField(max_length=255)
    query   = models.TextField()
    notes   = models.TextField(blank=True)
    stored_results  = models.TextField(blank=True, help_text='Tab-separated values. Include header row.')
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'atlas_viewer_utilities"."saved_query'
        verbose_name_plural = 'Saved queries'
        
    