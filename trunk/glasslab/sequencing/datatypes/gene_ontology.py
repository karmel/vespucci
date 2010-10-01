'''
Created on Sep 30, 2010

@author: karmel
'''
from django.db import models

class GoSeqEnrichedTerm(models.Model):
    '''
    GO term IDs and p-values from GoSeq analysis.
    '''
    go_term_id = models.CharField(max_length=20)
    p_value_overexpressed = models.FloatField()
    p_value_underexpressed = models.FloatField()
    
    @classmethod
    def set_table_name(cls, base_name):
        ''' 
        Set current table name based on CurrentPeak name.
        '''
        cls._meta.db_table = base_name + '_goseq'