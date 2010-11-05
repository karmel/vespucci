'''
Created on Sep 30, 2010

@author: karmel
'''
from django.db import models
from glasslab.utils.datatypes.basic_model import DynamicTable

class GoSeqEnrichedTerm(DynamicTable):
    '''
    GO term IDs and p-values from GoSeq analysis.
    '''
    go_term_id = models.CharField(max_length=20)
    p_value_overexpressed = models.FloatField()
    p_value_underexpressed = models.FloatField()
