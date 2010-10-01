'''
Created on Oct 1, 2010

@author: karmel
'''
from django.db import models
from glasslab.utils.datatypes.genome_reference import GenomeType

class BackgroundGOCount(models.Model):
    '''
    For all genes for a given genome_type, stores the expected appearance of GO terms 
    by ID, and the distance from the GO tree root.
    
    Used for determining whether sample GO term appearances are enriched or
    differently distributed.
    '''
    genome_type         = models.ForeignKey(GenomeType)
    go_term_id          = models.CharField(max_length=20)
    go_term             = models.CharField(max_length=255)
    appearance_count    = models.IntegerField(max_length=10)
    distance_from_root  = models.IntegerField(max_length=10)
    
    class Meta: db_table = 'gene_ontology_reference"."background_go_count'